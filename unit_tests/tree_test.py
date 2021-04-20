#!/bin/python3

import sys
sys.path.append(".")

from adder_graph import adder_graph as graph
from adder_graph import adder_node as node
from adder_tree import adder_tree as tree
import networkx as nx
import pydot

g = tree(8)
assert(g._checkLF(7,7)==(g[7,7],g[6,6]))
assert(g._checkLT(7,7)==(g[7,7],g[6,6]))
assert(g._checkLT(3)==(g[3,3],g[2,2]))
assert(g._checkLF(2,2)==(None,None))
assert(g._checkLT(2)==(None,None))

assert(g._checkFT(7)==(None,None))
assert(g._checkTF(7)==(None,None))
assert(g._checkFL(7)==(None,None))
assert(g._checkTL(7)==(None,None))

g.trim_layer()
g.LF(7)
g.compress()
g.LF(5)
g.compress()
g.LF(3)
g.compress()
g.LF(7)
g.compress()
g.LF(6)
g.compress()
g.LF(4)
g.compress()
g.trim_layer()
g.trim_layer()
g.trim_layer()
g.trim_layer()
g.add_layer()
g.trim_layer()

#pg=nx.drawing.nx_pydot.to_pydot(g)
#pg.write_png('output.png',prog='neato')