"""plugins.py."""
# ABOUTME: Type definitions for plugin instrumentation including call records and event generators.
# ABOUTME: Defines protocols and models for capturing function calls and generating extension events.

from typing import Any, Protocol, Tuple

from pydantic import BaseModel

from ._services import EventPayload, ExtensionEvent


class CallRecord(BaseModel):
    """Represent the Attributes of a Function/Method Call.

    Captures the function object, input parameters and result of a call
    to a wrapped function.

    There are times when the event generator function (or an event payload generator)
    needs the instance object in order to manipulate the result somehow. See AWS local
    simulator plugin for an example.

    if fn is a method from a an instance of class but not a class
    method.

    Ignores unbound methods and class methods for now for simplicity.

    Parameters
    ----------
    args: Tuple[Any, ...] | None
        Unnamed arguments passed to the wrapper function. Defaults to None
    fn: object | None
        The function object. Defaults to None.
    kwargs: dict[str, Any] | None
        Keyword arguments passed to the function fn. Defaults to None
    return_value: Any
        The value returned by the function.
    """

    args: Tuple[Any, ...] | None = None
    fn: object | None = None
    kwargs: dict[str, Any] | None = None
    return_value: Any | None


class EventPayloadGenerator(Protocol):
    """Event Payload Generator Function Type Definition."""

    def __call__(
        self,
        fn_call: CallRecord | None = None,
        **kwargs,
    ) -> EventPayload: ...


class EventGenerator(Protocol):
    """Event Generator Function Type Definition."""

    def __call__(
        self,
        fn_call: CallRecord | None = None,
        **kwargs,
    ) -> ExtensionEvent: ...
