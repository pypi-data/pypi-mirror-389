import mmodel
from mmodel.metadata import (
    MetaDataFormatter,
    format_value,
    format_func,
    format_modifierlist,
    format_shortdocstring,
    wrapper80,
)

nodeformatter = MetaDataFormatter(
    {
        "name": format_value,
        "node_func": format_func,
        "output": lambda k, value: [f"return: {value}"],
        "modifiers": format_modifierlist,
        "output_unit": lambda k, v: [f"return_unit: {v}"] if v else [],
        "doc": format_shortdocstring,
    },
    [
        "name",
        "_",
        "node_func",
        "output",
        "output_unit",
        "functype",
        "modifiers",
        "_",
        "doc",
    ],
    wrapper80,
    ["modifiers"],
)


class Node(mmodel.Node):
    """Node object with mrfmsim metadata formatting."""

    def __str__(self):
        """Modify the string representation to include unit."""
        return nodeformatter(self)
