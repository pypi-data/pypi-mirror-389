from mrfmsim.group import ExperimentGroup
from mrfmsim.node import Node
from mrfmsim import formula
from .stdelements import STANDARD_NODES, STANDARD_COMPONENTS

node_objects = [
    Node("minimum absolute x offset", func=formula.min_abs_offset, output="B_offset"),
    Node("rel_dpol sat", func=formula.rel_dpol_sat_steadystate, output="rel_dpol"),
    Node(
        "rel_dpol periodic_irrad",
        func=formula.rel_dpol_periodic_irrad,
        output="rel_dpol",
    ),
]


CermitESR_edges = [
    ["grid extended", "Bz extended"],
    ["Bz extended", "B_tot extended"],
    ["B_tot extended", ["B_offset extended", "B_tot sliced"]],
    ["B_tot sliced", "mz_eq"],
    [["B_offset extended", "x_0p window pts"], "minimum absolute x offset"],
    ["minimum absolute x offset", "rel_dpol sat"],
    [["mz_eq", "Bzxx", "rel_dpol sat"], "spring constant shift"],
    ["spring constant shift", "frequency shift"],
]
CermitESRStationaryTip_edges = [
    ["Bz", "B_tot"],
    ["B_tot", ["mz_eq", "B_offset"]],
    ["B_offset", "rel_dpol sat"],
    [["mz_eq", "Bzxx", "rel_dpol sat"], "spring constant shift"],
    ["spring constant shift", "frequency shift"],
]
CermitESRSmallTip_edges = [
    ["grid extended", "Bz extended"],
    ["Bz extended", "B_tot extended"],
    ["B_tot extended", ["B_offset extended", "B_tot sliced"]],
    ["B_tot sliced", "mz_eq"],
    [["B_offset extended", "x_0p window pts"], "minimum absolute x offset"],
    ["minimum absolute x offset", "rel_dpol sat"],
    [["mz_eq", "Bzxx trapz", "rel_dpol sat"], "spring constant shift trapz"],
    ["spring constant shift trapz", "frequency shift"],
]
CermitESRStationaryTipPulsed_edges = [
    ["Bz", "B_tot"],
    ["B_tot", ["mz_eq", "B_offset"]],
    ["B_offset", "rel_dpol periodic_irrad"],
    [["mz_eq", "Bzxx", "rel_dpol periodic_irrad"], "spring constant shift"],
    ["spring constant shift", "frequency shift"],
]

experiment_recipes = {
    "CermitESR": {
        "grouped_edges": CermitESR_edges,
        "doc": "CERMIT ESR experiment for a large tip.",
    },
    "CermitESRStationaryTip": {
        "grouped_edges": CermitESRStationaryTip_edges,
        "doc": "CERMIT ESR experiment for a stationary tip.",
    },
    "CermitESRSmallTip": {
        "grouped_edges": CermitESRSmallTip_edges,
        "doc": "CERMIT ESR experiment for a small tip.",
    },
    "CermitESRStationaryTipPulsed": {
        "grouped_edges": CermitESRStationaryTipPulsed_edges,
        "doc": "CERMIT ESR experiment for a stationary tip with a pulsed microwave.",
    },
}


components = {
    "magnet": ["Bz_method", "Bzx_method", "Bzxx_method"],
    "sample": ["J", "Gamma", "spin_density", "temperature", "dB_sat", "dB_hom"],
    "grid": [
        "grid_array",
        "grid_shape",
        "grid_step",
        "grid_voxel",
        "extend_grid_by_length",
    ],
    "cantilever": ["k2f_modulated"],
}

docstring = """\
Simulates a Cornell-style frequency shift magnetic resonance force microscope
experiment in which microwaves are applied for half a cantilever cyclic to
saturate electron spin resonance in a bowl-shaped region swept out by the
cantilever motion."""

CermitESRGroup = ExperimentGroup(
    "CermitESRGroup",
    list(STANDARD_NODES) + node_objects,
    experiment_recipes,
    {"components": STANDARD_COMPONENTS},
    doc=docstring,
)
