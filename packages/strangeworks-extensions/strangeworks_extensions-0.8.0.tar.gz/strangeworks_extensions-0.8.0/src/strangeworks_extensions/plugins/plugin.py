"""plugin.py."""

import logging
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class Status(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    INITALIZED = "initialized"


class ExtensionsPlugin(ABC):
    """Extensions Plugin Base Class."""

    def __init__(
        self,
        name: str,
        display_name: str | None = None,
    ):
        self._name: str = name
        self._display_name: str = display_name or self._name
        self._status: Status = Status.INITALIZED

    @abstractmethod
    def enable(self, *args, **kwargs): ...

    @abstractmethod
    def disable(self, *args, **kwargs): ...

    @property
    def name(self) -> str:
        return self._name

    @property
    def display_name(self) -> str:
        return self._display_name
