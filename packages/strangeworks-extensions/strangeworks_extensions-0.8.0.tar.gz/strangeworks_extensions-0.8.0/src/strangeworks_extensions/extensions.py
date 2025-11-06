"""extensions.py."""

import logging
from importlib.metadata import entry_points

from strangeworks_core.types import Resource, SDKCredentials

from strangeworks_extensions.products import Extension
from strangeworks_extensions.sdk.platform import get_resource_for_product

logger = logging.getLogger(__name__)
_extensions_plugins = {
    entry.name: entry for entry in entry_points(group="sdk-extensions")
}

_EXTENSIONS_KWARG_KEYWORD: str = "extensions"


def enable(extension: Extension, credentials: SDKCredentials):
    """Enable an SDK Extension."""
    resource: Resource = get_resource_for_product(
        product_slug=extension.value,
        creds=credentials,
    )

    plugin_ep = _extensions_plugins.get(extension.value)
    try:
        if plugin_ep:
            plugin_cls = plugin_ep.load()
            plugin_obj = plugin_cls(
                resource=resource,
                credentials=credentials,
            )
            print(f"Enabling SDK integration: {extension.value}")
            plugin_obj.enable()
        else:
            logger.debug(f"no plugin found for {extension.value}")
    except Exception as ex:
        logger.debug(f"error enabling extension for {extension.value}")
        logger.exception(ex)
    finally:
        return


def setup(*, credentials: SDKCredentials, **kwargs):
    """Set Up SDK Extensions."""
    enable_list: list[Extension] = kwargs.pop(_EXTENSIONS_KWARG_KEYWORD, [])
    if enable_list:
        for extension in enable_list:
            enable(extension=extension, credentials=credentials)
