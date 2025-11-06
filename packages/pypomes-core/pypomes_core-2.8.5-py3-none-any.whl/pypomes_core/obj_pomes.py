import inspect
import json
import os
import traceback
from contextlib import suppress
from contextvars import ContextVar
from functools import wraps
from types import TracebackType
from typing import Any


def obj_is_serializable(obj: Any) -> bool:
    """
    Determine if *obj* is serializable.

    :param obj: the reference object
    :return: *True* if serializable, *False* otherwise
    """
    # initialize the return variable
    result: bool = True

    # verify the object
    try:
        json.dumps(obj)
    except (TypeError, OverflowError):
        result = False

    return result


def obj_to_dict(obj: Any,
                omit_private: bool = True) -> dict[str, Any] | list[Any] | Any:
    """
    Convert the generic object *obj* to a *dict*.

    The conversion is done recursively. Attributes for which exceptions are raised on attempt
    to access them are silently omited.

    :param obj: the object to be converted
    :param omit_private: whether to omit private attributes (defaults to *True*)
    :return: the dict obtained from *obj*
    """
    # declare the return variable
    result: dict[str, Any] | list[Any] | Any

    if isinstance(obj, dict):
        result = {str(k): obj_to_dict(obj=v,
                                      omit_private=omit_private) for k, v in obj.items()}
    elif isinstance(obj, list | tuple | set):
        result = [obj_to_dict(obj=item,
                              omit_private=omit_private) for item in obj]
    elif hasattr(obj, "__dict__") or not isinstance(obj, str | int | float | bool | type(None)):
        result = {}
        for attr in dir(obj):
            if not (omit_private and attr.startswith("_")):
                with suppress(Exception):
                    value: Any = getattr(obj, attr)
                    if not callable(value):
                        result[attr] = obj_to_dict(obj=value,
                                                   omit_private=omit_private)
    else:
        result = obj

    return result


def exc_format(exc: Exception,
               exc_info: tuple[type[BaseException], BaseException, TracebackType]) -> str:
    """
    Format the error message resulting from the exception raised in execution time.

    The format to use: <python_module>, <line_number>: <exc_class> - <exc_text>

    :param exc: the exception raised
    :param exc_info: information associated with the exception
    :return: the formatted message
    """
    tback: TracebackType = exc_info[2]
    cls: str = str(exc.__class__)

    # retrieve the execution point where the exception was raised (bottom of the stack)
    tlast: traceback = tback
    while tlast.tb_next:
        tlast = tlast.tb_next

    # retrieve the module name and the line number within the module
    try:
        fname: str = os.path.split(p=tlast.tb_frame.f_code.co_filename)[1]
    except Exception:
        fname: str = "<unknow module>"
    fline: int = tlast.tb_lineno

    return f"{fname}, {fline}, {cls[8:-2]} - {exc}"


# initialize the context variables to hold parameter data
defaulted_params: ContextVar[list[str]] = ContextVar("defaulted_params")
specified_params: ContextVar[list[str]] = ContextVar("specified_params")


def capture_params(func: callable) -> callable:
    """
    Create a decorator to identify parameters in a function which were defaulted, and which were explicility passed.

    Introspect the call to *func* and make available two lists in context variables:
        - *defaulted_params*: parameters not passed, but defaulted as per their respective declarations
        - *specified_params*: parameters explicitly passed (named, positionally in *args*, or keyworded in *kwargs*)

    :param func: the function being decorated
    :return: the return from the call to *func*
    """
    @wraps(func)
    # ruff: noqa: ANN003 - Missing type annotation for *{name}
    def wrapper(*args, **kwargs) -> Any:

        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        # all parameters with defaults
        with_defaults: set[str] = {
            name for name, param in sig.parameters.items()
            if param.default is not inspect.Parameter.empty
        }

        # explicitly passed parameters (from bind, before defaults applied)
        explicitly_passed: set[str] = set(sig.bind(*args, **kwargs).arguments.keys())

        # parameters that used default values
        used_defaults: set[str] = with_defaults - explicitly_passed

        # store in context variables
        specified_params.set(list(explicitly_passed))
        defaulted_params.set(list(used_defaults))

        # proceeed executing the decorated function
        return func(*args, **kwargs)

    # prevent a rogue error ("View function mapping is overwriting an existing endpoint function")
    wrapper.__name__ = func.__name__

    return wrapper


# initialize the context variables to hold parameter data
defaulted_args: ContextVar[dict[str, Any]] = ContextVar("defaulted_args")
specified_args: ContextVar[dict[str, Any]] = ContextVar("specified_args")


def capture_args(func: callable) -> callable:
    """
    Create a decorator to identify arguments in a function which were defaulted, and which were explicility passed.

    Introspect the call to *func* and make available two dictionaries in context variables:
        - *defaulted_args*: arguments not passed, but defaulted as per their respective declarations
        - *specified_qrgs*: arguments explicitly passed (named, positionally in *args*, or keyworded in *kwargs*)

    :param func: the function being decorated
    :return: the return from the call to *func*
    """
    @wraps(func)
    # ruff: noqa: ANN003 - Missing type annotation for *{name}
    def wrapper(*args, **kwargs) -> Any:

        sig = inspect.signature(func)

        # bind only explicitly passed arguments
        bound_explicit = sig.bind(*args, **kwargs)
        bound_explicit.apply_defaults()

        # bind all arguments (with defaults applied)
        bound_all = sig.bind(*args, **kwargs)
        bound_all.apply_defaults()

        # All parameters with defaults
        with_defaults = {
            name for name, param in sig.parameters.items()
            if param.default is not inspect.Parameter.empty
        }

        # explicitly passed arguments
        explicitly_passed: dict[str, Any] = dict(bound_explicit.arguments)

        # arguments that used default values
        used_defaults: dict[str, Any] = {
            name: bound_all.arguments[name]
            for name in with_defaults
            if name not in explicitly_passed
        }

        # Store in context variables
        specified_args.set(explicitly_passed)
        defaulted_args.set(used_defaults)

        # proceeed executing the decorated function
        return func(*args, **kwargs)

    # prevent a rogue error ("View function mapping is overwriting an existing endpoint function")
    wrapper.__name__ = func.__name__

    return wrapper
