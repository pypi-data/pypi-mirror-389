"""types.py."""

from typing import Any, Protocol

from pydantic import BaseModel
from strangeworks_extensions.types import (
    CallRecord,
    EventGenerator,
    EventPayloadGenerator,
)


class ModuleSpec(BaseModel):
    module_name: str


class FunctionSpec(BaseModel):
    module_name: str
    function_name: str


class ClassMethodSpec(BaseModel):
    module_name: str
    class_name: str
    method_name: str


class RuntimeWrapper(Protocol):
    def __call__(
        self,
        *args,
        **kwargs,
    ) -> Any: ...


class URLSelector(Protocol):
    def __call__(self, url: str) -> bool: ...


class ProxySelector(Protocol):
    """Protocol for URL selectors with proxy capabilities."""

    def use_proxy(self, url: str) -> bool: ...

    @property
    def proxy_url(self) -> str: ...


__all__ = [
    "ModuleSpec",
    "FunctionSpec",
    "ClassMethodSpec",
    "RuntimeWrapper",
    "URLSelector",
    "ProxySelector",
    "CallRecord",
    "EventGenerator",
    "EventPayloadGenerator",
]
