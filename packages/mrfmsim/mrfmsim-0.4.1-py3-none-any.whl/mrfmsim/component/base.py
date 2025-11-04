"""Base component class."""

from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class ComponentBase:
    def __str__(self):
        """Reformat the ``dataclass`` string output.

        The default format is three decimal places for floats.
        For custom format, define the format in the field metadata.
        The ``dataclass``' ``__repr__`` is not being replaced.
        """

        str_lines = []
        for k, v in asdict(self).items():
            unit = self.get_unit(k)
            # use _ to avoid name conflict
            format_ = self._get_metadata(k).get("format", ".3f")
            if isinstance(v, float):
                # round the float values
                value = f"{v:{format_}}"
            elif isinstance(v, (list, np.ndarray)):
                # with np.set_printoptions(legacy="1.25", precision=3):
                v = np.array(v)
                value = np.array2string(
                    v,
                    suppress_small=True,
                    separator=", ",
                    formatter={"float": lambda x: f"{x:{format_}}"},
                )
            elif isinstance(v, str):
                value = repr(v)
            else:
                value = v

            str_lines.append(f"{k} = {value} {unit}".rstrip())
        return "{}\n  {}".format(
            self.__class__.__name__, "\n  ".join(str_lines).strip()
        )

    def _get_metadata(self, attr):
        """Get the metadata for the attribute.

        The metadata are defined in the fields of the
        dataclass attributes.
        """

        if attr in self.__dataclass_fields__:
            return self.__dataclass_fields__[attr].metadata
        else:
            return {}

    def get_unit(self, attr):
        """Get the units of the attributes.

        If the units are undefined, None is returned.
        """

        if hasattr(self, attr):
            return self._get_metadata(attr).get("unit", "")
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{attr}'"
            )
