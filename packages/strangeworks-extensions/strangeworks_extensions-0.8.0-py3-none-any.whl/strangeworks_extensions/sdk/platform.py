"""platform.py."""

from strangeworks_core.errors import StrangeworksError
from strangeworks_core.types import Resource, SDKCredentials

from strangeworks_extensions.sdk import _resource
from strangeworks_extensions.sdk._cfg_file import get_resource_from_config_file

from ._gql import SDKAPI


def get_resource_for_product(
    product_slug: str,
    creds: SDKCredentials,
) -> Resource:
    _preferred_resource_slug = get_resource_from_config_file(product_slug=product_slug)
    sdk = SDKAPI(api_key=creds.api_key, base_url=creds.host_url)
    res = _resource.get(
        sdk,
        resource_slug=_preferred_resource_slug,
        product_slug=product_slug,
    )
    if len(res) > 1 and _preferred_resource_slug is None:
        raise StrangeworksError("pick one")
    elif len(res) == 0 and _preferred_resource_slug is None:
        raise StrangeworksError("create one")

    return res[0]
