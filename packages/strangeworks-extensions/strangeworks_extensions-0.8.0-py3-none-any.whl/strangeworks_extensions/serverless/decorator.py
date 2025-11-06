"""decorator.py."""

import functools
import logging
from contextvars import ContextVar

from strangeworks_core.types import JobStatus, Resource, SDKCredentials

from strangeworks_extensions.sdk import get_resource_for_product, get_sdk_session
from strangeworks_extensions.serverless.types import IDExtractor
from strangeworks_extensions.types import EventPayload, EventType, ExtensionEvent
from strangeworks_extensions.types._services import Artifact

_SW_EXTENSIONS_ROUTER_PATH = "/products/sdk-extensions/jobs/create"

_credentials: ContextVar[SDKCredentials] = ContextVar[SDKCredentials]("_creds")

logger = logging.getLogger(__name__)


def set_credentials(api_key: str, host_url: str):
    """Set credentials for decorator.

    Parameters
    ----------
    api_key : str
        users workspace api key
    host_url : str
        base platform url (ex https://api.strangeworks.com)
    """
    global _credentials
    _credentials.set(SDKCredentials(api_key=api_key, host_url=host_url))


def sw_job(
    _func=None,
    *,
    product: str,
    tags: list[str] | None = None,
    credentials: SDKCredentials | None = None,
    get_remote_id: IDExtractor | None = None,
):
    _creds: SDKCredentials | None = credentials or _credentials.get()

    def _serverless_decorator(fn):
        @functools.wraps(fn)
        def _wrapper(*args, **kwargs):
            retval = fn(*args, **kwargs)
            try:
                if _creds:
                    resource: Resource = get_resource_for_product(
                        product_slug=product,
                        creds=_creds,
                    )
                    event: EventPayload = EventPayload(
                        artifacts=[
                            Artifact(
                                data={"args": args, "kwargs": kwargs},
                                name="args.json",
                            ),
                            Artifact(
                                data=retval,
                                name="result.json",
                            ),
                        ],
                        sw_status=JobStatus.COMPLETED,
                    )
                    req: ExtensionEvent = ExtensionEvent(
                        product_slug=product,
                        resource_slug=resource.slug,
                        event_type=EventType.COMPLETE,
                        payload=event,
                    )

                    _url: str = f"{_creds.host_url}{_SW_EXTENSIONS_ROUTER_PATH}"
                    with get_sdk_session(credentials=_creds) as session:
                        _res = session.post(
                            url=_url,
                            json=req.model_dump(
                                exclude_none=True,
                            ),
                            headers={
                                "Content-Type": "application/json",
                            },
                        )
                        _res.raise_for_status()
            except Exception as ex:
                logger.exception(ex)
            finally:
                return retval

        return _wrapper

    if _func is None:
        return _serverless_decorator
    else:
        return _serverless_decorator(_func)
