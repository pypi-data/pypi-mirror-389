from mrfmsim import Experiment, Graph, Node
from mrfmsim import formula
import operator

# For a single experiment, the nodes need to explicitly defined and
# matched to the graph edges. The shared nodes are not used here.

node_objects = [
    Node(
        "Bz", formula.field_func, inputs=["Bz_method", "grid_array", "h"], output="Bz"
    ),
    Node(
        "B_tot",
        operator.add,
        inputs=["Bz", "B0"],
        output="B_tot",
        doc="Calculate combined magnetic field.",
    ),
    Node(
        "Bzx",
        formula.field_func,
        inputs=["Bzx_method", "grid_array", "h"],
        output="Bzx",
    ),
    Node("Bzx squared", lambda Bzx: Bzx**2, output="Bzx2", doc="Bzx squared."),
    Node("mz_eq", formula.mz_eq, output="mz_eq"),
    Node("mz2_eq", formula.mz2_eq, output="mz2_eq"),
    Node("B offset", formula.B_offset, output="B_offset"),
    Node("rel_dpol ibm_cyclic", formula.rel_dpol_ibm_cyclic, output="rel_dpol"),
    Node(
        "force signal",
        formula.sum_of_product,
        inputs=["Bzx", "rel_dpol", "mz_eq", "spin_density", "grid_voxel"],
        output="dF_spin",
    ),
    Node(
        "force variance signal",
        formula.sum_of_product,
        inputs=["Bzx2", "rel_dpol", "mz2_eq", "spin_density", "grid_voxel"],
        output="dF2_spin",
    ),
]

grouped_edges = [
    ["Bz", "B_tot"],
    ["B_tot", ["mz_eq", "B offset"]],
    ["B offset", "rel_dpol ibm_cyclic"],
    [["mz_eq", "Bzx", "rel_dpol ibm_cyclic"], "force signal"],
    ["Bzx", "Bzx squared"],
    [["Bzx squared", "rel_dpol ibm_cyclic", "mz2_eq"], "force variance signal"],
]


docstring = "Simulate an IBM-style cyclic-inversion magnetic resonance force microscope experiment."
components = {
    "magnet": ["Bz_method", "Bzx_method"],
    "sample": ["J", "Gamma", "spin_density", "temperature"],
    "grid": ["grid_array", "grid_voxel"],
}

IBMCyclic_graph = Graph(name="ibm_cyclic_graph")
IBMCyclic_graph.add_grouped_edges_from(grouped_edges)
IBMCyclic_graph.add_node_objects_from(node_objects)


IBMCyclic = Experiment(
    "IBMCyclic",
    IBMCyclic_graph,
    doc=docstring,
    components=components,
)
