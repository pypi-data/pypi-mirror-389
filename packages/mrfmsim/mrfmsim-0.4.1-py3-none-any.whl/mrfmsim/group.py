from mrfmsim.model import Experiment, experimentformatter
from mrfmsim.graph import Graph
import mmodel
from functools import partial
from mmodel.metadata import (
    wrapper80,
    format_value,
    format_dictkeys,
    MetaDataFormatter,
    format_group_content
)


experimentgroupformatter = MetaDataFormatter(
    {
        "name": format_value,
        "experiments": format_dictkeys,
        "nodes": format_dictkeys,
        "experiment_defaults": partial(format_group_content, formatter=experimentformatter),
        "doc": format_value,
    },
    ["name", "experiments", "nodes", "experiment_defaults", "_", "doc"],
    wrapper80,
    ["experiment_defaults", "nodes"],
)


class ExperimentGroup(mmodel.ModelGroup):
    """Create a group of experiments.

    The class inherits from mmodel.ModelGroup with the mrfmsim graph and node.
    """

    model_type = Experiment
    graph_type = Graph

    def __init__(
        self, name, node_objects, experiment_recipes, experiment_defaults=None, doc=""
    ):
        super().__init__(
            name, node_objects, experiment_recipes, experiment_defaults, doc
        )

    @property
    def experiments(self):
        """Return the models dictionary."""
        return self._models

    @property
    def experiment_defaults(self):
        """Return the defaults dictionary."""
        return self._model_defaults

    def __str__(self):
        return experimentgroupformatter(self)
