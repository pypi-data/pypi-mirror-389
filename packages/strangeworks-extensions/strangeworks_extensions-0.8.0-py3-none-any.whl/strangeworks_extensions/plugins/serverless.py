import atexit
import inspect
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

from strangeworks_core.platform.session import StrangeworksSession
from strangeworks_core.types import SDKCredentials
from strangeworks_extensions.sdk import get_sdk_session as get_session
from strangeworks_extensions.types import CallRecord, EventGenerator, ExtensionEvent

_SW_EXTENSIONS_ROUTER_PATH = "/products/sdk-extensions/jobs/create"

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="sw-event-sender")
_pending_futures: set = set()


def _shutdown_executor():
    """Shutdown the executor gracefully before Python exits."""
    _executor.shutdown(wait=True, cancel_futures=False)


atexit.register(_shutdown_executor)

__all__ = ["local_call_handler", "wait_for_pending_events"]


def wait_for_pending_events(timeout: float | None = None):
    """Wait for all pending event submissions to complete.

    Parameters
    ----------
    timeout : float | None
        Maximum time to wait in seconds. If None, waits indefinitely.

    Notes
    -----
    This function is primarily intended for testing to ensure all background
    HTTP requests have completed before making assertions.
    """
    if not _pending_futures:
        return

    for future in as_completed(_pending_futures, timeout=timeout):
        # Just consume the futures to ensure they're done
        try:
            future.result()
        except Exception:
            # Exceptions are already logged in _send_event
            pass

    _pending_futures.clear()


def local_call_handler(
    credentials: SDKCredentials,
    event_generator: EventGenerator,
    url_path: str | None = _SW_EXTENSIONS_ROUTER_PATH,
):
    """Handles results from locally made function/method calls and submits them
    to the extensions service.

    Parameters
    ----------
    credentials : SDKCredentials
        credentials to use for this workspace.
    payload_generator : ResultAdapter
        function that processes results and generates an extensions
        service request.
    url_path: str | None
        URL path to use. Will use the resource url path if none provided.
    event_type: EventType = EventType.COMPLETE
    """

    def _send_event(fn, args, kwargs, res):
        """Send event to extensions service in background thread."""
        try:
            logger.debug("processing results to generate extensions request")

            req: ExtensionEvent = event_generator(
                fn_call=(
                    CallRecord(
                        args=args,
                        kwargs=kwargs,
                        fn=(
                            fn.__self__
                            if inspect.ismethod(fn)
                            and not isinstance(fn.__self__, type)
                            else fn
                        ),
                        return_value=res,
                    )
                ),
            )

            logger.debug(f"generated extensions request: {req}")

            sw_session: StrangeworksSession = get_session(
                credentials=SDKCredentials(
                    host_url=credentials.host_url, api_key=credentials.api_key
                ),
            )
            _path = url_path or _SW_EXTENSIONS_ROUTER_PATH
            _url: str = urljoin(credentials.host_url, _path)
            logger.debug(f"url: {_url}")

            _res = sw_session.request(
                method="POST",
                url=_url,
                json=req.model_dump(exclude_none=True),
                headers={
                    "Content-Type": "application/json",
                },
            )
            _res.raise_for_status()

        except Exception as ex:
            if logger.level == logging.DEBUG:
                logger.exception(ex)

    def _wrapper(fn, *args, **kwargs):
        logger.info(f"[PATCHED] {fn.__name__} args={args}, kwargs={kwargs}")

        res = fn(*args, **kwargs)

        # Submit event sending to background thread pool and track the future
        future = _executor.submit(_send_event, fn, args, kwargs, res)
        _pending_futures.add(future)

        # Remove completed futures to prevent memory leaks
        _pending_futures.difference_update({f for f in _pending_futures if f.done()})

        return res

    return _wrapper
