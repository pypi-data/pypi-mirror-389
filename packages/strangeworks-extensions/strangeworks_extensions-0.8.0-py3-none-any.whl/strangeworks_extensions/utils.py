"""utils.py."""

import logging
import time
import uuid

logger = logging.getLogger()


def request_id() -> str:
    """Generate Request ID

    Generaters a unique-enough string to be used as an identifier.

    Returns
    -------
    str
       a unique identifier
    """
    ts = int(time.time() * 1000)  # milliseconds
    return f"{ts:x}-{uuid.uuid4().hex[:8]}"


def add_logger(fn, *args, **kwargs):
    """Instrument Given Function/Method with a Logger.

    Any call to the function will generate a log entry with function name, and
    arguments. Take care to make sure no sensitive information is passed in
    with the arguments.

    Parameters
    ----------
    fn : function
        Function/class method to instrument.

    Returns
    -------
    Any | None:
        The value returned by the given function or method.
    """
    logger.info(f"[PATCHED] {fn.__name__} args={args}, kwargs={kwargs}")
    result = fn(*args, **kwargs)
    return result
