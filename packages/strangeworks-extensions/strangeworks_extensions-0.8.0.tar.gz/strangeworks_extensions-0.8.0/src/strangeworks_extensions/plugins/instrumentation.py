"""instrumentation.py."""

import logging
from importlib.util import find_spec
from typing import Callable

from strangeworks_extensions.plugins import runtime
from strangeworks_extensions.plugins.plugin import ExtensionsPlugin, Status
from strangeworks_extensions.plugins.types import (
    ClassMethodSpec,
    FunctionSpec,
    RuntimeWrapper,
)

logger = logging.getLogger(__name__)


class Instrumentation(ExtensionsPlugin):
    def __init__(
        self,
        name: str,
        handler_func: RuntimeWrapper,
        spec: FunctionSpec | ClassMethodSpec | None = None,
        **kwargs,
    ):
        super().__init__(name=name, **kwargs)
        self._spec = spec
        self._handler_fn = handler_func
        self._original_fn: Callable | None = None

    def enable(
        self,
        **kwargs,
    ):
        """ "Enable Plugin."""
        _handler_function: RuntimeWrapper = kwargs.pop("handler_function", None)
        _spec: FunctionSpec | ClassMethodSpec = kwargs.pop("spec", self._spec)
        if _spec is None:
            logger.warning("no spec available")
            return

        if self._status in [Status.INITALIZED, Status.DISABLED]:
            api_spec = find_spec(_spec.module_name)
            if api_spec:
                logger.debug(f"enabling pluging {self._name}")
                self._original_fn = runtime.wrap(
                    _spec,
                    wrapper=_handler_function or self._handler_fn,
                )
                if self._original_fn:
                    self._status = Status.ENABLED
                    logging.debug(f"instrumentation successful {self._name}")
            else:
                logger.debug(
                    "unable to find module spec {_spec.module_name} for {self._name}"  # noqa
                )

    def disable(self, **kwargs):
        """Disable plugin"""
        if self._status in [Status.ENABLED] and self._original_fn:
            runtime.unwrap(self, spec=self._spec, fn=self._original_fn)
            self._status = Status.DISABLED
