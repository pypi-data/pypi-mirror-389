"""__init__.py."""

from strangeworks_core.platform.auth import Authenticator, get_sdk_authenticator
from strangeworks_core.platform.session import StrangeworksSession
from strangeworks_core.types import SDKCredentials

from .platform import get_resource_for_product


def get_sdk_session(credentials: SDKCredentials):
    sdk_auth: Authenticator = get_sdk_authenticator(base_url=credentials.host_url)
    return StrangeworksSession(
        host=credentials.host_url, api_key=credentials.api_key, authenticator=sdk_auth
    )


__all__ = [
    "get_sdk_session",
    "get_resource_for_product",
]
