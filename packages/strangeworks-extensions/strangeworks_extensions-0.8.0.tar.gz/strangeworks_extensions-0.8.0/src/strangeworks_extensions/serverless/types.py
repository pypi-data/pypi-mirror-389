"""types.py."""

from typing import Any, Protocol


class IDExtractor(Protocol):
    """Defines a Function that extracts the remote ID of a job."""

    def __call__(self, *args: Any, **kwds: Any) -> str:
        """
        Extracts the remote ID from the result of a job creation call.

        The function should process the result and return the remote ID associated with \
        the job.

        Returns
        -------
        str
            The remote ID of the job.
        """
        ...
