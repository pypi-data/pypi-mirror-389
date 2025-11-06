import logging
from importlib.util import find_spec

from strangeworks_core.types import SDKCredentials

from strangeworks_extensions.plugins.instrumentation import Instrumentation
from strangeworks_extensions.plugins.requests.proxy import (
    RequestAPIHandler,
    get_proxy_redirect_wrapper,
)
from strangeworks_extensions.plugins.types import (
    ClassMethodSpec,
    FunctionSpec,
    ModuleSpec,
    ProxySelector,
    RuntimeWrapper,
    URLSelector,
)

logger = logging.getLogger(__name__)

_function_spec = FunctionSpec(module_name="requests.api", function_name="request")


def _create_proxy_selector(url_selector: URLSelector, proxy_url: str) -> ProxySelector:
    class _Selector:
        def __init__(self, url_selector, proxy_url: str):
            self._url_selector: URLSelector = url_selector
            self._proxy_url = proxy_url

        def use_proxy(self, url: str) -> bool:
            return self._url_selector(url)

        @property
        def proxy_url(self):
            return self._proxy_url

    return _Selector(url_selector=url_selector, proxy_url=proxy_url)


class RequestAPIPlugin(Instrumentation):
    """Requests Instrumentation Class.

    Parameters
    ----------
    Instrumentation :
        extends Instrumentation class.
    """

    def __init__(
        self,
        spec: ModuleSpec,
        selector: URLSelector,
        proxy_url: str,
        credentials: SDKCredentials,
        handler_fn: RequestAPIHandler | None = None,
        name: str = "requests_plugin",
        **kwargs,
    ):
        handler_fn = handler_fn or get_proxy_redirect_wrapper(
            selector=_create_proxy_selector(
                url_selector=selector,
                proxy_url=proxy_url,
            ),
            credentials=credentials,
        )
        super().__init__(
            name=name,
            handler_func=handler_fn,
            **kwargs,
        )
        self._spec = spec

    def enable(
        self,
        handler_fn: RuntimeWrapper | None = None,
    ):
        api_spec = find_spec(self._spec.module_name)
        if api_spec:
            logger.debug(f"enabling requests plugin {self._name}")
            self._original_fn = self.enable(
                FunctionSpec(module_name="requests.api", function_name="request"),
                handler_function=handler_fn or self._handler_fn,
            )


class CustomSessionPlugin(Instrumentation):
    """Instrument Custom Extensions of Requests Session class.

    Parameters
    ----------
    Instrumentation :
        extends Instrumentation class
    """

    def __init__(
        self,
        spec: ClassMethodSpec,
        selector: URLSelector,
        proxy_url: str,
        credentials: SDKCredentials,
        name: str = "custom_session_plugin",
        handler_fn: RequestAPIHandler | None = None,
        **kwargs,
    ):
        handler_fn = handler_fn or get_proxy_redirect_wrapper(
            selector=_create_proxy_selector(
                url_selector=selector,
                proxy_url=proxy_url,
            ),
            credentials=credentials,
        )
        super().__init__(
            name=name,
            handler_func=handler_fn,
            spec=spec,
            **kwargs,
        )
