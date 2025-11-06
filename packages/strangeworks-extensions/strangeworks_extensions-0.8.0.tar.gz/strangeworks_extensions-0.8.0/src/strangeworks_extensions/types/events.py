"""events.py."""
# ABOUTME: Factory protocol for creating event generators from resources.
# ABOUTME: Used to construct event generators that can be configured per-resource basis.

from typing import Protocol

from strangeworks_core.types import Resource

from .plugins import EventGenerator


class GeneratorFactory(Protocol):
    def __call__(
        self,
        resource: Resource,
        **kwargs,
    ) -> EventGenerator: ...
