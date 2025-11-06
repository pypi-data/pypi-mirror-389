"""config_file.py."""

import os
import tomllib
from typing import Any

DEFAULT_CFG_FILE_PATH = "~/.config/strangeworks/sdk/cfg.toml"
CFG_FILE_PATH = os.path.expanduser(
    os.getenv("STRANGEWORKS_CONFIG_PATH", DEFAULT_CFG_FILE_PATH)
)


def get_resource_from_config_file(
    product_slug: str, file_path: str = CFG_FILE_PATH
) -> str | None:
    """Get Selected Resource for Product.

    If there are multiple resources for a product in a workspace and the user has
    already selected one, this function will return that resource slug.

    Parameters
    ----------
    product_slug: str
        Product slug

    Returns
    -------
    : str | None
        The selected resource slug or None if there aren't any.
    """
    if product_slug in ["api_key", "url"]:
        return None
    with open(file_path, "rb") as f:
        config: dict[str, Any] = tomllib.load(f)
        profile: str = str(config.get("active_profile"))
        if profile:
            workspace = config.get(profile)
            if workspace:
                return workspace.get(product_slug)
        return None
