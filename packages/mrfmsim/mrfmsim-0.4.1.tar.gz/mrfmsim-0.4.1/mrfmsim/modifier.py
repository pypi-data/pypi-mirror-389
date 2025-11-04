from mmodel.utility import param_sorter
from functools import wraps
import numba as nb
from inspect import Parameter, signature, Signature
from pprint import pformat
from copy import deepcopy
from collections import defaultdict
import mmodel


def replace_component(replacement: dict, allow_duplicate=False):
    """Modify the signature with components.

    The modifier modifies the internal model function. The wrapper
    function is keyword-only. The function by default does not
    allow duplicated signature. If we want to replace several
    attributes with a component, the component name cannot exist
    in the original signature. For example, if we have a function

        def func(a, b, obj):
            return a + b, obj

    and we want to replace a and b with a component, we cannot
    name the component "obj".

    In rares that we do want to replace a, b with a component,

        def func(obj):
            return obj.a + obj.b, obj

        func(obj=obj)

    we would have to use "obj_obj" as the component name. The
    result function is equivalent to

        def func(obj_obj, obj):
            return obj_obj.a + obj_obj.b + obj

        func(obj_obj=obj, obj=obj)

    The behavior is very confusing to users. The solution is to
    replace the components, but leave the original "obj" signature
    as it is. In the final signature, the duplicated signatures
    are combined into one. The solution here is to add a boolean
    flag allow_duplicate. If the flag is set to True, the function
    allows duplicated signatures.

    The solution, however, leaves another ambiguity. If we indeed
    want to replace the component with the same name, but use
    the original name with an attribute:

        def func(obj):
            return obj.a + obj.b, obj.obj

        func(obj=obj)

    We have decided that this behavior is not allowed regardless the flag.
    Because in this case, in an inspection attempt, it is confusing to
    understand if the obj is the original obj or an attribute to the new obj.
    In this case, a new object name should be used.

    :param dict[str] replacement: in the format of
        {component_object: [replacement_attribute1, replacement_attribute2, ...]}
    """

    def modifier(func):
        sig = signature(func)
        params = sig.parameters  # immutable

        new_params_dict = dict(params)  # mutable
        replacement_dict = defaultdict(list)

        # in the event that the duplication is allowed
        # and the component is already in the signature
        # the list is maintained for the wrapped function
        duplicated_copmp = []
        for comp, rep_attrs in replacement.items():

            if not allow_duplicate:
                # check duplication last
                assert (
                    comp not in params
                ), f"parameter {repr(comp)} already in the signature"

            elif comp in params:
                duplicated_copmp.append(comp)
            # new_params_dict[comp] = Parameter(comp, 1)

            for attr in rep_attrs:
                # check attr
                # the error is related to the component dictionary
                # definition, regardless of the target function signature
                if attr == comp:
                    raise ValueError(
                        f"attribute name cannot be the same as component {repr(comp)}"
                    )
                if attr in params:
                    replacement_dict[comp].append(attr)
                    new_params_dict.pop(attr, None)
                    # overwrite if duplicated
                    new_params_dict[comp] = Parameter(comp, 1)

        @wraps(func)
        def wrapped(**kwargs):
            for comp, rep_attrs in replacement_dict.items():
                if comp in duplicated_copmp:
                    comp_obj = kwargs[comp]
                else:
                    comp_obj = kwargs.pop(comp)
                for attr in rep_attrs:
                    kwargs[attr] = getattr(comp_obj, attr)

            return func(**kwargs)

        wrapped.__signature__ = Signature(
            parameters=sorted(new_params_dict.values(), key=param_sorter)
        )
        # deepcopy to prevent modification
        wrapped.param_replacements = deepcopy(replacement_dict)
        return wrapped

    modifier.metadata = f"replace_component({pformat(replacement)})"
    return modifier


def numba_jit(**kwargs):
    """Numba jit modifier with keyword arguments.

    Add metadata to numba.jit. The numba decorator outputs
    all the parameters make it hard to read.
    Use the decorator the same way as numba.jit().
    """

    @mmodel.modifier.add_modifier_metadata("numba_jit", **kwargs)
    def decorator(func):
        func = nb.jit(**kwargs)(func)
        return func

    return decorator
