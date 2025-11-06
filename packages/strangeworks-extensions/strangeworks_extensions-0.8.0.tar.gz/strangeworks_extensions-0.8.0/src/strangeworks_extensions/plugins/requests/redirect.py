"""redirect.py."""

import logging

from requests import sessions
from strangeworks_core.types import SDKCredentials

from strangeworks_extensions.plugins import runtime
from strangeworks_extensions.plugins.types import FunctionSpec, ProxySelector
from strangeworks_extensions.products import Extension
from strangeworks_extensions.sdk import get_sdk_session
from strangeworks_extensions.utils import request_id

_DEFAULT_SPEC = FunctionSpec(module_name="requests.api", function_name="request")

logger = logging.getLogger(__name__)


class ProxyPlugin:
    """Redirect certain requests to a Strangeworks proxy instead of original
    destination."""

    _singleton = None
    _registry: dict[Extension, ProxySelector] = {}

    def __new__(cls):
        if cls._singleton is None:
            cls._singleton = super().__new__(cls)
        return cls._singleton

    def __init__(
        self,
        credentials: SDKCredentials | None = None,
    ):
        self._spec = _DEFAULT_SPEC
        self._credentials: SDKCredentials | None = credentials
        # self._orig_fn = self._do_instrument()
        self._orig_fn = runtime.wrap(self._spec, self)

    def set_credentials(self, credentials: SDKCredentials):
        self._credentials = credentials

    @classmethod
    def enable(cls, product: Extension, selector: ProxySelector):
        cls._registry[product] = selector

    @classmethod
    def disable(cls, product: Extension):
        cls._registry.pop(product, None)

    def _use_proxy(self, url: str) -> str | None:
        for product, selector in ProxyPlugin._registry.items():
            logger.debug(f"check for proxy (url: {url}, product: {product})")
            if selector.use_proxy(url):
                return selector.proxy_url
        return None

    def __call__(self, fn, method: str, url: str, *args, **kwargs):
        proxy_url: str | None = self._use_proxy(url=url)
        if proxy_url and self._credentials:
            logger.debug(
                f"use strangeworks proxy: {fn.__name__}, method: {method}, url: {url} args: {args}, kwargs: {kwargs}"  # noqa
            )
            req = {
                "id": request_id(),
                "provider_request": {
                    "method": method,
                    "url": url,
                    "kwargs": kwargs,
                },
            }
            with get_sdk_session(
                credentials=self._credentials,
            ) as session:
                return session.request(
                    method="POST",
                    url=proxy_url,
                    json=req,
                )

        logger.debug(
            f"passthrough {fn.__name__}, method: {method}, url: {url} args: {args}, kwargs: {kwargs}"  # noqa
        )
        with sessions.Session() as session:
            return session.request(method=method, url=url, *args, **kwargs)
