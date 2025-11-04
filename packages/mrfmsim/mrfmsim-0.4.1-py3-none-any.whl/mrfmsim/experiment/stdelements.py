"""For experiments with shared nodes, some nodes are housed here.

It is possible to put all the nodes here, however, it is not recommended to do that
because that would make it difficult to read and debug.
For some single operations, instead of using lambda, here we define it explicitly.

Here we store the nodes in a tuple to avoid accidental modification of the nodes.

There are two types of node groups. One with extended grid that is
used for calculate the cantilever motion and one without.

The nodes can be overridden by appending with a Node of the same name.
This behavior is allowed in the individual w    
"""

from mrfmsim.node import Node
from mrfmsim import formula
import operator


def extend_grid_by_length_x(extend_grid_by_length, mw_x_0p):
    """Extend the grid by the given length in x."""
    return extend_grid_by_length([mw_x_0p, 0, 0])


STANDARD_NODES = (
    # standard and extended field calculation
    Node(
        "grid extended",
        extend_grid_by_length_x,
        output="ext_grid",
    ),
    Node(
        "Bz",
        formula.field_func,
        inputs=["Bz_method", "grid_array", "h"],
        output="Bz",
    ),
    Node(
        "Bz extended",
        formula.field_func,
        inputs=["Bz_method", "ext_grid", "h"],
        output="ext_Bz",
    ),
    Node(
        "Bzx",
        formula.field_func,
        inputs=["Bzx_method", "grid_array", "h"],
        output="Bzx",
    ),
    Node(
        "Bzx extended",
        formula.field_func,
        inputs=["Bzx_method", "ext_grid", "h"],
        output="ext_Bzx",
    ),
    Node(
        "Bzxx",
        formula.field_func,
        inputs=["Bzxx_method", "grid_array", "h"],
        output="Bzxx",
    ),
    Node("Bzxx trapz", formula.xtrapz_field_gradient, output="Bzxx_trapz"),
    Node(
        "B_tot",
        operator.add,
        inputs=["Bz", "B0"],
        output="B_tot",
        doc="Calculate combined magnetic field.",
    ),
    Node(
        "B_tot extended",
        operator.add,
        inputs=["ext_Bz", "B0"],
        output="ext_B_tot",
        doc="Calculate combined magnetic field extended.",
    ),
    Node(
        "B_tot sliced",
        formula.slice_matrix,
        inputs=["ext_B_tot", "grid_shape"],
        output="B_tot",
        doc="Calculate combined magnetic field.",
    ),
    Node("B_offset", func=formula.B_offset, output="B_offset"),
    Node(
        "B_offset extended",
        formula.B_offset,
        inputs=["ext_B_tot", "f_rf", "Gamma"],
        output="ext_B_offset",
    ),
    Node(
        "x_0p window pts",
        func=formula.convert_grid_pts,
        inputs=["mw_x_0p", "grid_step"],
        output="ext_pts",
    ),
    # signal
    Node("mz_eq", func=formula.mz_eq, output="mz_eq"),
    Node(
        "spring constant shift",
        formula.neg_sum_of_product,
        inputs=["Bzxx", "rel_dpol", "mz_eq", "spin_density", "grid_voxel"],
        output="dk_spin",
        doc="Calculate dk_spin account for the negative sign in the approximation.",
    ),
    Node(
        "spring constant shift trapz",
        formula.sum_of_product,
        inputs=["Bzxx_trapz", "rel_dpol", "mz_eq", "spin_density", "grid_voxel"],
        output="dk_spin",
    ),
    Node(
        "frequency shift",
        operator.mul,
        inputs=["dk_spin", "k2f_modulated"],
        output="df_spin",
        doc="Convert the spring constant shift to frequency shift.",
    ),
)

STANDARD_COMPONENTS = {
    "magnet": ["Bz_method", "Bzx_method", "Bzxx_method", "mu0_Ms", "magnet_origin"],
    "sample": [
        "J",
        "Gamma",
        "spin_density",
        "temperature",
        "T1",
        "T2",
        "dB_sat",
        "dB_hom",
    ],
    "grid": [
        "grid_array",
        "grid_voxel",
        "grid_shape",
        "grid_step",
        "extend_grid_by_length",
    ],
    "cantilever": ["k2f_modulated"],
}
