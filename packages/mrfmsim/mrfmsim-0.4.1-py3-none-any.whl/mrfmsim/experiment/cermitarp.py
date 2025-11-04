from mrfmsim import formula
from mrfmsim import Node, ExperimentGroup
from .stdelements import STANDARD_NODES, STANDARD_COMPONENTS

node_objects = [
    Node(
        "rel_dpol arp",
        formula.rel_dpol_arp,
        output="rel_dpol",
    )
]

CermitARP_edges = [
    ["Bz", "B_tot"],
    ["B_tot", ["mz_eq", "B_offset"]],
    ["B_offset", "rel_dpol arp"],
    [["mz_eq", "Bzxx", "rel_dpol arp"], "spring constant shift"],
]

CermitARPSmallTip_edges = [
    ["Bz", "B_tot"],
    ["B_tot", ["mz_eq", "B_offset"]],
    ["B_offset", "rel_dpol arp"],
    [["mz_eq", "Bzxx trapz", "rel_dpol arp"], "spring constant shift trapz"],
]

experiment_recipes = {
    "CermitARP": {
        "grouped_edges": CermitARP_edges,
        "doc": "Simulate CERMIT ARP for a large tip.",
    },
    "CermitARPSmallTip": {
        "grouped_edges": CermitARPSmallTip_edges,
        "doc": "Simulate CERMIT ARP for a small tip.",
    },
}

docstring = """\
Simulates a Cornell-style frequency-shift magnetic resonance 
force microscope experiment in which a single frequency-sweep adiabatic 
rapid passage through resonance is used to invert the spins.
"""

CermitARPGroup = ExperimentGroup(
    "CermitARPGroup",
    node_objects=list(STANDARD_NODES) + node_objects,
    experiment_recipes=experiment_recipes,
    experiment_defaults={"components": STANDARD_COMPONENTS},
    doc=docstring,
)
