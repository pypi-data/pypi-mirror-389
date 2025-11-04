from mrfmsim import formula
import operator
from mrfmsim import ExperimentGroup, Node

node_objects = [
    Node(
        "field",
        formula.xtrapz_field_gradient,
        output="field",
    ),
    Node(
        "spring constant shift",
        lambda field, Gamma, J: -Gamma * J * 1.054571628e-7 * field,
        output="dk_spin",
    ),
    Node(
        "effective force shift",
        formula.singlespin_analytical,
        output="dF_spin",
    ),
    Node(
        "effective spring constant shift",
        operator.truediv,
        inputs=["dF_spin", "x_0p"],
        output="dk_spin",
        doc="Calculate the effective spring constant shift.",
    ),
]

experiment_recipes = {
    "CermitSingleSpinApprox": {
        "grouped_edges": [
            ["field", "spring constant shift"],
        ],
        "doc": "Approximated solution with Trapezoid rules for single spin CEMRIT ESR. "
        "The experiment is for a single spin located directly under a spherical magnet.",
    },
    "CermitSingleSpin": {
        "grouped_edges": [
            ["effective force shift", "effective spring constant shift"],
        ],
        "doc": "Full spring constant solution using analytical expression. "
        "The experiment is for a single spin located directly under a spherical magnet.",
    },
}


components = {
    "magnet": ["magnet_radius", "mu0_Ms", "magnet_origin", "Bzx_method"],
    "sample": ["Gamma", "J"],
}


docstring = """\
Simulates an MRFM experiment in the "hangdown" or SPAM geometry
where a single electron spin is located directly below the tip. With a
small tip, the motion of the cantilever is not negligible on the scale of 
the magnet tip and the tip sample separation. We evaluate the full 
expression for the change in cantilever frequency including the effect of 
the oscillating cantilever tip. 
"""


CermitSingleSpinGroup = ExperimentGroup(
    name="CermitSingleSpinGroup",
    node_objects=node_objects,
    experiment_recipes=experiment_recipes,
    experiment_defaults={"components": components},
    doc=docstring,
)
