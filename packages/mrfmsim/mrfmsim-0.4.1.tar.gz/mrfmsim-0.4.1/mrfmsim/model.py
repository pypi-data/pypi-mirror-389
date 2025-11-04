"""Experiment Class

The class inherits from ``mmodel.Model`` class to add certain functionality and defaults.
"""

import mmodel
from mrfmsim.modifier import replace_component
import networkx as nx
from mmodel.metadata import (
    MetaDataFormatter,
    format_dictargs,
    format_func,
    format_modifierlist,
    format_obj_name,
    format_returns,
    format_value,
    wrapper80,
)
import copy


experimentformatter = MetaDataFormatter(
    {
        "self": format_func,
        "returns": format_returns,
        "graph": format_obj_name,
        "handler": format_obj_name,
        "handler_kwargs": format_dictargs,
        "modifiers": format_modifierlist,
        "doc": format_value,
    },
    [
        "self",
        "returns",
        "return_units",
        "group",
        "graph",
        "handler",
        "handler_kwargs",
        "modifiers",
        "_",
        "doc",
    ],
    wrapper80,
    ["modifiers", "handler_kwargs"],
)


class Experiment(mmodel.Model):
    """Experiment class for mrfmsim.

    The class inherits from mmodel.Model with minor modifications.
    The handler defaults to MemHandler, and in plotting, the method defaults
    to draw_graph.
    """

    def __init__(
        self,
        name,
        graph,
        handler=mmodel.MemHandler,
        handler_kwargs: dict = None,
        modifiers: list = None,
        returns: list = None,
        param_defaults: dict = {},
        doc: str = "",
        components: dict = {},
        allow_duplicated_components: bool = False,
        **kwargs,
    ):

        super().__init__(
            name,
            graph,
            handler,
            handler_kwargs,
            modifiers,
            returns,
            param_defaults,
            doc,
            allow_duplicated_components=allow_duplicated_components,
            **kwargs,
        )

        # components need to be deepcopied
        self._components = components

        if components:
            # Add the component modification to modifiers.
            component_mod = replace_component(components, allow_duplicated_components)
            self.model_func = component_mod(self.model_func)
            self._param_replacements = self.model_func.param_replacements

        # add units for return values
        self.return_units = {}
        for node, output in nx.get_node_attributes(self.graph, "output").items():
            if output in self.returns:
                unit = getattr(self.get_node_object(node), "output_unit", None)
                if unit:
                    self.return_units[output] = unit

    @property
    def components(self):
        """Return a deepcopy of the components.

        The values of the dictionary contains lists.
        """
        return copy.deepcopy(self._components)

    @property
    def param_replacements(self):
        """Return a deepcopy of the parameter replacements.

        Components can contain more than the actual parameters being
        replaced. The param_replacements is the final replacement dictionary.
        """
        return copy.deepcopy(self._param_replacements)

    def __str__(self):
        return experimentformatter(self)
