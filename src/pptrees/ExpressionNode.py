from .modules import *
from .util import parse_net, verso_pin

class ExpressionNode:
    """Defines a node in an expression tree

    Attributes:
        children (list): A list of child nodes
            Note that this list is ordered for trees,
            and the first child is leftmost
        parent (ExpressionNode): The parent node
        value (str): The value of the node; a module name
        leafs (int): An integer encoding all leafs reachable from this node
        block (int): The block number of this node's HDL (if applicable)
        in_nets (list): A list of input nets
        out_nets (list): A list of output nets
        x_pos (float): The x-coordinate of this node's graphical representation
        y_pos (float): The y-coordinate of this node's graphical representation
    """
    def __init__(self, value, x_pos=0, y_pos=0):
        """Initializes a new ExpressionNode

        Args:
            value (str): The value of the node; a valid module name
            x_pos (float): The x-coordinate of this node's graphical representation
            y_pos (float): The y-coordinate of this node's graphical representation
        """
        if not isinstance(x_pos, (int, float)):
            raise TypeError("X-coordinate must be a number")
        if not isinstance(y_pos, (int, float)):
            raise TypeError("Y-coordinate must be a number")
        if value not in modules:
            raise ValueError("Invalid module name: {}".format(value))

        # Node attributes
        self.value = value
        self.children = []
        self.parent = None

        # HDL-related attributes
        self.in_nets = {x: [None] * y for x, y, *z in modules[value]["ins"]}
        self.out_nets = {x: [None] * y for x, y in modules[value]["outs"]}

        # Graph-related attributes
        self.leafs = 0
        self.block = None

        # Visualization-related attributes
        self.x_pos = x_pos
        self.y_pos = y_pos

    def __str__(self):
        """Returns a string representation of this node"""
        return self.__repr__()

    def __repr__(self):
        """Returns a string representation of this node"""
        return "{0}_{1}_{2}".format(self.value, self.x_pos, self.y_pos)

    def __lt__(self, other):
        """Compares this node to another node by position in tree

        Args:
            other (ExpressionNode): The node to compare to

        Returns:
            bool: Whether or not this node is further right than the other node
        """
        return self.leafs < other.leafs

    def __gt__(self, other):
        """Compares this node to another node by position in tree

        Args:
            other (ExpressionNode): The node to compare to

        Returns:
            bool: Whether or not this node is further left than the other node
        """
        return self.leafs > other.leafs

    def __iter__(self):
        """Iterates over the children of this node"""
        for c in self.children:
            yield c

    def __getitem__(self, key):
        """Returns the child node at the given index"""
        return self.children[key]

    def morph(self, value):
        """Morphs this node to a new value

        This will error out if the node has a parent or children.
        """
        if self.parent is not None or \
                any([not x is None for x in self.children]):
            raise ValueError("Cannot morph a node with children or parents")
        if value not in modules:
            raise ValueError("Invalid module name: {}".format(value))

        # Create new node
        new_node = ExpressionNode(value, self.x_pos, self.y_pos)
        new_node.leafs = self.leafs
        new_node.block = self.block

        return new_node

    def add_child(self, child, pin1, pin2, net_name):
        """Adds a child node to this node

        Args:
            child (ExpressionNode): The child node to add
            pin1 (tuple): (name, index) of the parent pin
            pin2 (tuple): (name, index) of the child pin
            net_name (str): Fall-back net name, if it does not exist
        """

        # Break the pins apart into names and indices
        pn1, pi1 = pin1
        pn2, pi2 = pin2

        if pn1 not in self.in_nets or pn2 not in child.out_nets:
            raise ValueError("Invalid pin connection")

        ## Check if net already exists
        if not (self.in_nets[pn1][pi1] is None):
            net_name = self.in_nets[pn1][pi1]
        elif not (child.out_nets[pn2][pi2] is None):
            net_name = child.out_nets[pn2][pi2]

        ## Assign net name to ports
        self.in_nets[pn1][pi1] = net_name
        child.out_nets[pn2][pi2] = net_name

        # If nodes are not already connected, connect them
        if not child.parent is self:
            try:
                index = self.children.index(None)
                self.children[index] = child
            except ValueError:
                self.children.append(child)
            child.parent = self
            # Recalculate leafs recursively
            self._recalculate_leafs()

        return net_name

    def remove_child(self, child):
        """Removes a child node from this node

        Args:
            child (ExpressionNode): The child node to remove
        """

        # Remove child/parent connection
        index = self.children.index(child)
        self.children[index] = None
        child.parent = None

        # Reset net names in parent (inpins only!)
        for pn, pins in self.in_nets.items():
            # Check if port is connected to this child
            vrs = verso_pin(pn)
            if vrs not in child.out_nets:
                continue
            # If so, query the port pin by pin
            for pi in range(len(pins)):
                net = pins[pi]
                if pi is None:
                    continue
                if net in child.out_nets[vrs]:
                    pins[pi] = None

        # Recalculate leafs recursively
        self._recalculate_leafs()

    def iter_down(self, fun):
        """Calls a function on this node and all descendants

        Args:
            fun (function): The function to call on each child
        """
        fun(self)
        for c in self.children:
            if c is not None:
                c.iter_down(fun)

    ### NOTE: THIS ASSUMES THAT PARENTS AND CHILDREN ARE FULLY CONNECTED
    ### TO-DO: Handle case of partially connected nodes
    def _recalculate_leafs(self, leafs=0):
        """Recalculates the leafs of this node and its parents"""
        self.leafs = leafs
        for c in self.children:
            if c is None:
                continue
            self.leafs = self.leafs | c.leafs
        if self.parent is not None:
            self.parent._recalculate_leafs()

    def hdl(self, language="verilog",flat=False):
        """Returns the HDL of this node

        Args:
            language (str): The language in which to generate the HDL
            flat (bool): If True, flatten the node's HDL

        Returns:
            str: The HDL of this node
            list: Set of HDL module definitions used in the node
        """
        if not flat and language == "verilog":
            return (self._verilog(), (modules[self.value][language],))
        if not flat and language == "vhdl":
            return (self._vhdl(), (modules[self.value][language],))
        if flat and language == "verilog":
            return (self._verilog_flat(), set())
        if flat and language == "vhdl":
            return (self._vhdl_flat(), set())

    def _verilog(self):
        """Return single line of Verilog consisting of module instantiation"""

        # Instantiate module
        ret = "\t{0} U0 (".format(self.value)

        # Create list of all instance pins and copy in unformatted net IDs
        pins = self.in_nets.copy()
        pins.update(self.out_nets)

        # Format net IDs into the module instantiation
        for a in pins:
            b = ','.join([parse_net(x) for x in pins[a]])
            ret += " .{0}( {{ {1} }} ),".format(a,b)
        ret = ret[:-1] + " );\n"

        return ret

    def _vhdl(self):
        """Return single line of VHDL consisting of module instantiation"""

        # Instantiate module
        ret = "\tU0: {0}\n".format(self.value)
        ret += "\t\tport map ("

        # Create list of all instance pins and copy in unformatted net IDs
        pins = self.in_nets.copy()
        pins.update(self.out_nets)

        # Format net IDs into the module instantiation
        for a in pins:
            for b in range(len(pins[a])):
                net_name = parse_net(pins[a][b])
                ret += "\n\t\t\t{0}({1}) => {2},".format(a, b, net_name)

        # Close parenthesis
        ret = ret[:-1] + "\n\t\t);\n"

        return ret

    def _verilog_flat(self):
        """Return Verilog consisting of the module's internal logic"""

        ### Grab only instantiated cells from the HDL definiton

        # Iterate over each line in the HDL definition
        hdl_def = modules[self.value][language].splitlines()

        # Flag whether we're currently looking at a cell
        in_std_cell = False

        # Store the filtered HDL in a string
        ret = ""

        for l in hdl_def:
            if "assign" in l or "<=" in l:
                ret += l + "\n"
            else:
                if "U" in l:
                    in_std_cell = True
                if in_std_cell == True:
                    ret += l + "\n"
                if l != "" and l[-1] == ";":
                    in_std_cell = False

        # Create list of all instance pins and copy in unformatted net IDs
        pins = self.ins.copy()
        pins.update(self.outs)

        # Format net IDs and replace them into module's HDL
        for a in pins:
            if len(pins[a]) == 1:
                net_name = parse_net(pins[a][0])
                ret = ret.replace(a, net_name)
            else:
                for b in range(len(pins[a])):
                    net_name = parse_net(pins[a][b])
                    ret = ret.replace("{0}[{1}]".format(a, b), net_name)

        return ret[:-1]

if __name__ == "__main__":
    raise RuntimeError("This module is not intended to be run directly")
