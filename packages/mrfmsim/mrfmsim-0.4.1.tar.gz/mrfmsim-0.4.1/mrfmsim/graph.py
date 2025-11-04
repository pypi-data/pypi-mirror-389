import mmodel
from mrfmsim.node import Node


class Graph(mmodel.Graph):
    """Graph object."""

    graph_attr_dict_factory = {"graph_module": "mrfmsim", "node_type": Node}.copy
