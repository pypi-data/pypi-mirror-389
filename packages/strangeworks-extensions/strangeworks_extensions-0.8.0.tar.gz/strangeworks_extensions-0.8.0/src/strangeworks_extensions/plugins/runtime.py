"""runtime.py."""

import functools
import inspect
import logging
from functools import singledispatch
from typing import Any

from strangeworks_extensions.plugins.types import (
    ClassMethodSpec,
    FunctionSpec,
    RuntimeWrapper,
)

__all__ = ["wrap", "unwrap"]
logger = logging.getLogger(__name__)


@singledispatch
def wrap(
    spec: Any,
    wrapper: RuntimeWrapper,
):
    """Instrument function/method.

    Instruments the function or method identified by the given spec with the wrapper
    function provided.

    Parameters
    ----------
    spec : FunctionSpec | ClassMethodSpec
        contains info to identify which function/method to instrument
    wrapper : RuntimeWrapper
        wraps the function/method. .
    """
    raise NotImplementedError(
        f"Unable to wrap {type(wrapper)}: unsupported spec type {type(spec)}"
    )


@wrap.register
def _(
    spec: FunctionSpec,
    wrapper: RuntimeWrapper,
):
    """Instrument a Python Function."""
    try:
        # Import the module
        module = __import__(spec.module_name, fromlist=[""])

        # Get the original function
        original_function = getattr(module, spec.function_name)

        # Create wrapper
        @functools.wraps(original_function)
        def wrapped_function(*args, **kwargs):
            return wrapper(original_function, *args, **kwargs)

        # Replace the function in the module
        setattr(module, spec.function_name, wrapped_function)

        logger.debug(f"Patched {spec.module_name}.{spec.function_name}")
        return original_function
    except ModuleNotFoundError:
        # ignore ... ok if module not found
        return None
    except Exception as ex:
        logger.debug(f"Failed to patch {spec.module_name}.{spec.function_name}: {ex}")
        return None


@wrap.register
def _(
    spec: ClassMethodSpec,
    wrapper: RuntimeWrapper,
):
    """Instrument a method in a Python class."""
    try:
        # import module, get class ...
        module = __import__(spec.module_name, fromlist=[spec.class_name])
        class_obj = getattr(module, spec.class_name)

        # Get the original method
        original_method = getattr(class_obj, spec.method_name)

        # Create a wrapper function
        @functools.wraps(original_method)
        def wrapped_method(self, *args, **kwargs):
            return wrapper(original_method.__get__(self, class_obj), *args, **kwargs)

        # Replace the method
        setattr(class_obj, spec.method_name, wrapped_method)
        logger.debug(f"Patched {spec.class_name}.{spec.method_name}")

        return original_method
    except ModuleNotFoundError:
        # ignore ... ok if module not found
        return None
    except Exception as ex:
        logger.debug(f"Failed to patch {spec.class_name}.{spec.method_name}: {ex}")
        return None


@singledispatch
def unwrap(spec: Any, fn):
    """Rollback Instrumentation.

    Parameters
    ----------
    spec : FunctionSpec | ClassMethodSpec
        identifies the function/method to undo instrumentation on.
    fn:
        the function to replace teh instrumented function/method. Typically the
        original function/method before it was insturmented.
    """
    raise NotImplementedError(f"unsupported spec type {type(spec)}")


@unwrap.register
def _(spec: FunctionSpec, fn):
    if fn and inspect.isfunction(fn):
        try:
            module = __import__(spec.module_name, fromlist=[""])
            setattr(module, spec.function_name, fn)
        except Exception as ex:
            logger.exception(ex)
        finally:
            ...
    return


@unwrap.register
def _(spec: ClassMethodSpec, fn):
    if fn and inspect.ismethod(fn):
        try:
            module = __import__(spec.module_name, fromlist=[spec.class_name])
            class_obj = getattr(module, spec.class_name)
            setattr(class_obj, spec.method_name, fn)
        except Exception as ex:
            logger.exception(ex)
        finally:
            ...

    return
