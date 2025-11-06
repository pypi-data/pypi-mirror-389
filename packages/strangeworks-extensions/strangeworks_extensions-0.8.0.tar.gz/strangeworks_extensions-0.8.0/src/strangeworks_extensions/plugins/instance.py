import functools
import logging
import types

from strangeworks_extensions.plugins.plugin import ExtensionsPlugin, Status
from strangeworks_extensions.plugins.types import RuntimeWrapper

logger = logging.getLogger(__name__)


class InstanceInstrumentation(ExtensionsPlugin):
    def __init__(
        self,
        name: str,
        method_name: str,
        handler_func: RuntimeWrapper,
        instance: object,
        **kwargs,
    ):
        """Initialize Objects


        Parameters
        ----------
        name : str
            Name of the plugin.
        method_name : str
            Name of the method to instrument.
        handler_func : HandlerFunction
            Function to use for instrumentation.
        instance : _type_
            Instance whose method will be instrumented.
        """
        if not hasattr(instance, method_name):
            raise AttributeError(f"Instance has no method '{self._method_name}'")
        super().__init__(name=name, **kwargs)
        self._method_name: str = method_name
        self._handler_func: RuntimeWrapper = handler_func
        self._instance = instance
        self._original_method = None

    def enable(
        self,
        **kwargs,
    ):
        """Enable Instrumentation on an Instance Method.

        Returns
        -------
        None
            Object to enable/disable instrumentation on an instance method.
        """
        _original_method = getattr(self._instance, self._method_name)
        self._original_method = _original_method
        _handler_fn = self._handler_func

        # Create the patched method
        @functools.wraps(self._original_method)
        def updated_method(self, *args, **kwargs):
            return _handler_fn(_original_method, *args, **kwargs)

        # Bing updated method to the instance
        setattr(
            self._instance,
            self._method_name,
            types.MethodType(updated_method, self._instance),
        )
        self._status = Status.ENABLED

    def disable(self, *args, **kwargs):
        """_Disable Instrumentation of an Intance Method.

        Removes instrumentation and restores the instance method to its original.
        """
        setattr(self._instance, self._method_name, self._original_method)
        self._status = Status.DISABLED
