from contextlib import AbstractContextManager
from datetime import datetime, timedelta
from typing import Callable, Iterable, Iterator, Optional

from prosper_api.client import Client
from prosper_api.models import Listing, SearchListingsRequest

__all__ = ["AllocationStrategy"]


def _lender_yield_sort(listing: Listing) -> bool:
    return listing.lender_yield


class AllocationStrategy(AbstractContextManager, Iterable[Listing]):
    """Defines a partial order over the set of active prosper listings.

    Specifically, it defines a sequence of prosper API calls to get listings and an optional sort method used to reorder them before emission. Use the timeout parameter to force a maximum time to wait for matching listings.
    """

    def __init__(
        self,
        client: Client,
        api_param_iterator: Iterator[SearchListingsRequest],
        local_sort: Optional[Callable[[Listing], bool]] = None,
        timeout_seconds: float = -1.0,
    ):
        """Gets an instance of AllocationStrategy.

        Args:
            client (Client): Prosper API client
            api_param_iterator (Iterator[SearchListingsRequest]): Iterates over the different parameters to pass the Listing api.
            local_sort (Optional[Callable[[Listing], bool]]): Sorts the returned listings into the desired final order before returning.
            timeout_seconds (float): The max real time in seconds to try to get a listing before giving up. `-1` (default) indicates not timeout is required.
        """
        if local_sort is None:
            local_sort = _lender_yield_sort
        self._client = client
        self._api_param_iterator = api_param_iterator
        self._local_sort = local_sort
        self._end_time = (
            datetime.now() + timedelta(seconds=timeout_seconds)
            if timeout_seconds > 0
            else None
        )
        self._params: Optional[SearchListingsRequest] = None
        self._buffer: Optional[Iterable[Listing]] = None

    def __next__(self) -> Listing:
        """Gets the next listing from the buffer or fetches a new one if needed and available.

        This method enforces the timeout set at instantiation.
        """
        if self._end_time is not None:
            if datetime.now() > self._end_time:
                raise StopIteration("Timed out while searching listings")

        if self._buffer is None:
            self._params = self._api_param_iterator.__next__()
            result = sorted(
                self._client.search_listings(self._params).result, key=self._local_sort
            )
            if len(result) == 0:
                raise StopIteration("Not more listings")
            self._buffer = iter(result)

        return next(self._buffer)

    def __iter__(self):
        """Implements the iterable interface."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Does nothing yet."""
        return None
