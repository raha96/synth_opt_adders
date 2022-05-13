import re
import pathlib
import shutil
import importlib.resources

import networkx as nx

from .ExpressionNode import ExpressionNode
from .modules import *
from .util import hdl_syntax, hdl_entity, hdl_arch, hdl_inst
from .util import parse_net, sub_brackets, sub_ports
from .util import natural_keys

class ExpressionGraph(nx.DiGraph):
    """Defines a di-graph of arithmetic expressions

    The graph is defined as follows:
    - Each node is a module that computes an arithmetic expression
    - Each edge is a net connecting two modules

    Attributes:
        name (string): The name of the graph
        next_net (int): The next net name to be used
        next_block (int): The next block name to be used
        blocks (list): The list of blocks in the graph
        in_ports (list of ((string, int), string)): The list of input ports
        out_ports (list of ((string, int), string)): The list of output ports
    """

    def __init__(self, name="graph", in_ports=None, out_ports=None):
        """Initializes the graph

        Specifying in_ports and out_ports is optional.
        Doing so implies that the graph is already connected inside of a larger
        structure.
        If they are not specified, the graph will finds its own.

        Args:
            name (string): The name of the graph
            in_ports (list of tuples): The list of input ports
            out_ports (list of tuples): The list of output ports
        """

        # Make sure that in_ports and out_ports are both None or both lists
        if any(x is not None for x in [in_ports, out_ports]) and \
                not all(x is not None for x in [in_ports, out_ports]):
            raise ValueError(("in_ports and out_ports"
                "must both be None or both be lists"))

        super().__init__()

        self.name = name

        # Save the input and output ports
        self.in_ports = in_ports
        self.out_ports = out_ports

        # Procedurally-generated net names start with "n1"
        self.next_net = 1

        # Procedurally-generated block names start with "block1"
        self.next_block = 0
        self.blocks = [None]

    def add_node(self, node, **attr):
        """Adds a node to the graph

        Args:
            node (ExpressionNode): The name of the node to add
            attr (dict): The attributes of the node to add
        """

        if not isinstance(node, ExpressionNode):
            raise TypeError("Node must be an ExpressionNode")

        # Add GraphViz attributes
        kwargs = modules[node.value]
        kwargs.update(attr)
        kwargs["shape"] = kwargs.get("shape", "square")
        kwargs["fillcolor"] = kwargs.get("fillcolor", "white")
        kwargs["label"] = kwargs.get("label", "")
        kwargs["style"] = kwargs.get("style", "filled")
        kwargs["pos"] = "{0},{1}!".format(node.x_pos*-1, node.y_pos*-1)

        # Add the node to the graph
        super().add_node(node, **kwargs)
        return node

    def remove_node(self, node):
        """Removes a node from the graph

        Args:
            node (ExpressionNode): The name of the node to remove
        """

        if not isinstance(node, ExpressionNode):
            raise TypeError("Node must be an ExpressionNode")
        
        # Remove the node from the graph
        super().remove_node(node)
        return node

    def add_edge(self, parent, pin1, child, pin2):
        """Adds a directed edge to the graph, from parent to child

        Args:
            parent (ExpressionNode): The name of the first node
            pin1 (tuple): (name, index) of the pin on the first node
            child (ExpressionNode): The name of the second node
            pin2 (tuple): (name, index) of the pin on the second node
        """

        if not isinstance(parent, ExpressionNode):
            raise TypeError("Node1 must be an ExpressionNode")
        if not isinstance(child, ExpressionNode):
            raise TypeError("Node2 must be an ExpressionNode")

        # Connect the nodes
        proposed_net_name = "$n{0}_{1}".format(self.next_net, self.name)
        net_name = parent.add_child(child, pin1, pin2, proposed_net_name)
        if proposed_net_name == net_name:
            self.next_net += 1

        # Styles the edge for GraphViz visualization
        kwargs = {
            "arrowhead": "none",
            "ins": [pin1],
            "outs": [pin2],
            "edge_nets": [net_name]
        }

        # Initialize weight to parasitc delay
        # This is later modified by logical effort and cross-track cap
        kwargs["fanout"] = 1
        kwargs["tracks"] = 0
        kwargs["delay"] = modules[child.value]["pd"]
        kwargs["weight"] = kwargs["delay"]

        # If the two nodes are already connnected, simply update the pins
        if self.has_edge(parent, child):
            edge_data = self.get_edge_data(parent, child, default = kwargs)
            edge_data["ins"].append(pin1)
            edge_data["outs"].append(pin2)
            edge_data["edge_nets"].append(net_name)
        else:
        # Add the edge to the graph
            super().add_edge(parent, child, **kwargs)

        return self.get_edge_data(parent, child)

    def remove_edge(self, parent, child):
        """Removes an edge from the graph

        Args:
            parent (ExpressionNode): The parent node
            child (ExpressionNode): The child node
        """

        if not isinstance(parent, ExpressionNode):
            raise TypeError("Node1 must be an ExpressionNode")
        if not isinstance(child, ExpressionNode):
            raise TypeError("Node2 must be an ExpressionNode")
        if not self.has_edge(parent, child):
            raise ValueError("Edge does not exist")

        # Save the edge data
        edge_data = self.get_edge_data(parent, child)

        # Remove the edge from the graph
        super().remove_edge(parent, child)

        # Remove the edge from the nodes
        parent.remove_child(child)

        # Return the edge data
        return edge_data

    ### NOTE: Improve the heuristic used herein
    def update_edge_weight(self, parent, child):
        """Updates the weight of an edge from parent to child

        Args:
            parent (ExpressionNode): The parent node
            child (ExpressionNode): The child node
        """

        if not isinstance(parent, ExpressionNode):
            raise TypeError("Node1 must be an ExpressionNode")
        if not isinstance(child, ExpressionNode):
            raise TypeError("Node2 must be an ExpressionNode")
        if not self.has_edge(parent, child):
            raise ValueError("Edge does not exist")

        edge_data = self.get_edge_data(parent, child)

        ### This is a bad estimate of delay
        weight = edge_data["delay"] * edge_data["fanout"] + \
            edge_data["delay"] * edge_data["tracks"]

        edge_data["weight"] = weight

        return weight

    def add_block(self, *nodes):
        """Creates a new module block of nodes

        This is a sub-graph of nodes that will be flattened together into a
        single monolithic module.

        Args:
            nodes (list): The list of nodes to add to the block
        """
        if not all([isinstance(node, ExpressionNode) for node in nodes]):
            raise TypeError("Nodes must be ExpressionNodes")
        if not all([node.block is None for node in nodes]):
            raise ValueError("Nodes must not already be in a block")

        # If the block is empty, don't create it
        if not nodes:
            return None
        
        # Get the name of the block
        block_id = self.next_block

        # Assign the block to the nodes
        for node in nodes:
            node.block = block_id

        # Create the block
        new_block = self.subgraph(nodes)
        self.blocks[block_id] = new_block
        if block_id == len(self.blocks) - 1:
            self.blocks.append(None)

        # Increment the next block name
        self.next_block = next(
                x for x in range(len(self.blocks)) if self.blocks[x] is None
        )

        return block_id

    def remove_block(self, block_id):
        """Removes a block from the graph

        Args:
            block_id (int): The ID of the block to remove
        """
        if block_id not in range(len(self.blocks)) or self.blocks[block_id] is None:
            raise ValueError("Invalid block ID")

        # Remove the block from the graph
        block = self.blocks[block_id]
        for node in block:
            node.block = None
        self.blocks[block_id] = None

    def reset_blocks(self):
        """Removes all blocks from the graph"""

        # Remove all blocks from the graph
        for block_id in [x for x in self.blocks if x is not None]:
            self.remove_block(block_id)

        # Reset the next block name
        self.next_block = 0
        self.blocks = [None]

    def _get_internal_nets(self):
        """Returns the internal nets of the graph"""

        # Get all nets in the graph
        in_nets = set()
        out_nets = set()

        # Get the nets from nodes
        for node in self.nodes:
            for net in node.in_nets.values():
                in_nets.update([parse_net(x) for x in net])
            for net in node.out_nets.values():
                out_nets.update([parse_net(x) for x in net])

        # Get the nets from blocks
        for block in [x for x in self.blocks if x is not None]:
            block_in_nets, block_out_nets = block._get_internal_nets()
            in_nets.update(block_in_nets)
            out_nets.update(block_out_nets)

        # If the graph has pre-defined ports, filter them out
        if self.in_ports is not None:
            in_ports = [x[0][0] for x in self.in_ports]
            in_nets = [x for x in in_nets if x.split("[")[0] not in in_ports]
            out_ports = [x[0][0] for x in self.out_ports]
            out_nets = [x for x in out_nets if x.split("[")[0] not in out_ports]

        return (set(in_nets), set(out_nets))

    def _get_ports(self):
        """Returns the ports of the graph"""

        # If the ports are defined, return them
        if self.in_ports is not None:
            return (self.in_ports, self.out_ports)

        # Otherwise, find them from nodes and blocks
        in_ports, out_ports = self._get_internal_nets()

        # Signals generated inside this graph are not inputs
        in_ports = in_ports - out_ports

        # Form the ports
        # Assume that all these retrieved nets are 1-bit
        in_internal = [(sub_brackets(x),1) for x in in_ports]
        in_external = list(in_ports)
        in_ports = (in_internal, in_external)

        out_internal = [(sub_brackets(x),1) for x in out_ports]
        out_external = list(out_ports)
        out_ports = (out_internal, out_external)

        return (in_ports, out_ports)

    def hdl(
        self,
        out=None,
        mapping="behavioral",
        language="verilog",
        flat=False,
        full_flat=False,
        module_name=None,
        description_string="start of unnamed graph"
    ):
        """Creates a HDL description of the graph

        Args:
            language (str): The language in which to generate the HDL
            flat (bool): If True, flatten the graph's HDL
            full_flat (bool): If True, flatten all modules in the graph's HDL
            module_name (str): The name of the module to generate
            description_string (str): String commend to prepend to the HDL

        Returns:
            str: HDL module definition representing the graph
            list: Set of HDL module definitions used in the graph

        """
        # Check that the language is supported
        if language not in ["verilog", "vhdl"]:
            raise ValueError("Unsupported hardware-descriptive language")

        # Set language-specific syntax
        syntax = hdl_syntax[language]

        # If module name is not defined, set it to graph's name
        if module_name is None:
            module_name = self.name

        # Create the HDL

        hdl = ""
        module_defs = set()

        # Pull in the HDL description of blocks
        for block_id in range(len(self.blocks)):
            if self.blocks[block_id] is None:
                continue
            block = self.blocks[block_id]

            block_hdl, block_defs = block.hdl(
                    language=language,
                    flat=full_flat,
                    full_flat=True,
                    module_name=module_name + "_block_" + str(block_id),
                    description_string="block {0}".format(block_id)
            )

            hdl += block_hdl
            module_defs.update(block_defs)

        # Pull in the HDL description of nodes outside of blocks
        # If fully flattening them, need to rename "w*" internal wires
        if full_flat:
            w_ctr = 0
        for node in self:
            if node.block is not None:
                continue
            node_hdl, node_defs = node.hdl(
                    language=language,
                    flat=full_flat
            )
            if full_flat:
                node_hdl = node_hdl.replace("w1", "w{0}".format(w_ctr))
                w_ctr += 1

            hdl += node_hdl
            module_defs.update(node_defs)

        # This HDL description will have multiple instances in it
        # By default, util.hdl_inst names all instances "U0"
        # These names need to be made unique
        U_count = 0
        good_hdl = ""
        while True:
            # Find the next instance name
            U = re.search(r"U\d+", hdl)
            if U is None:
                break
            # Replace it with the next name
            good_hdl += hdl[:U.start()] + "U" + str(U_count)
            hdl = hdl[U.end():]
            U_count += 1
        hdl = good_hdl + hdl

        # Add wire definitions
        in_wires, out_wires = self._get_internal_nets()
        wires = in_wires | out_wires
        wires = sorted(list(wires), key=natural_keys)

        wire_hdl = syntax["wire_def"].format(", ".join(wires))

        # Assemble the HDL
        hdl = syntax["comment_string"] + description_string + "\n" + \
                "\t" + wire_hdl + "\n" + hdl

        # If flat HDL is desired, it can returned here
        if flat:
            hdl = sub_ports(hdl, self.in_ports + self.out_ports)
            return hdl, module_defs

        # Otherwise, return the HDL module definition
        hdl, module_defs, file_out_hdl = self._wrap_hdl(hdl, module_defs,
                language, module_name)

        # Write the HDL to file
        if out is not None:
            self._write_hdl(file_out_hdl, out, language, mapping)

        return hdl, module_defs

    def _wrap_hdl(self, hdl, module_defs, language="verilog", module_name=None):
        """Wraps the HDL in a module definition"""

        # If flat HDL is not desired, wrap the graph in a module
        ## First get in_ports and out_ports
        (in_ports, out_ports) = self._get_ports()
        entity_ins = [x[0] for x in in_ports]
        entity_outs = [x[0] for x in out_ports]
        ## Then create the entity
        entity = hdl_entity(module_name, entity_ins, entity_outs, language)
        ## Then create the architecture
        arch = hdl_arch(module_name, hdl, language)
        ## Add the entity and architecture to the module_defs
        file_out_hdl = entity + arch + "".join(module_defs)
        module_defs.add(entity + arch)
        ## Create an instance of the module
        inst_ports = [[x[0][0],x[1]] for x in in_ports + out_ports]
        inst = hdl_inst(module_name, inst_ports, language)
        ## Add the instance to the HDL
        hdl = inst

        return hdl, module_defs, file_out_hdl

    def _write_hdl(self, file_out_hdl, out=None, language="verilog",
            mapping="behavioral"):
        """Writes the HDL to a file"""
        # Check that output path is valid
        if out is None:
            raise ValueError("Output path must be defined")

        # Set language-specific syntax
        syntax = hdl_syntax[language]
        
        outdir = pathlib.Path(out).resolve().parent
        if not outdir.exists():
            raise ValueError("Output path does not exist")

        # Verify that the mapping is supported
        file_suffix = syntax["file_extension"]
        mappings_path = importlib.resources.path("pptrees", "mappings")
        with mappings_path as pkg_map_dir:
            pkg_map_file = pkg_map_dir / (mapping + "_map" + file_suffix)
            local_map_file = outdir / (mapping + "_map" + file_suffix)

            if not pkg_map_file.is_file():
                raise ValueError("Unsupported mapping requested")

            # Copy the mapping file to the output directory
            shutil.copy(pkg_map_file, local_map_file)
    
        with open(out, "w") as f:
            f.write(file_out_hdl)

if __name__ == "__main__":
    raise RuntimeError("This module is not intended to be run directly")
