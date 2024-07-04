from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from logging import getLogger
from typing import Callable, Dict, Iterable, Iterator, NamedTuple, Optional, Union

from prosper_api.client import Client
from prosper_api.models import Listing, SearchListingsRequest

from prosper_bot.util import round_down_to_nearest_cent

_BASE_REQUEST = SearchListingsRequest(
    limit=10,
    biddable=True,
    invested=False,
    sort_by="lender_yield",
    sort_dir="desc",
)

__all__ = [
    "AllocationStrategy",
    "AllocationStrategies",
    "FixedTargetAllocationStrategy",
    "HighestMatchingRateAllocationStrategy",
]

logger = getLogger(__file__)


class AllocationStrategy(Iterable[Listing]):
    """Defines a partial order over the set of active prosper listings.

    Specifically, it defines a sequence of prosper API calls to get listings and an optional sort method used to
    reorder them before emission. Use the timeout parameter to force a maximum time to wait for matching listings.
    """

    def __init__(
        self,
        client: Client,
        search_request_iterator: Iterator[SearchListingsRequest],
        local_sort: Optional[Callable[[Listing], bool]] = None,
        timeout_seconds: float = -1.0,
    ):
        """Gets an instance of AllocationStrategy.

        Args:
            client (Client): Prosper API client
            search_request_iterator (Iterator[SearchListingsRequest]): Iterates over the different parameters to pass
                the Listing api.
            local_sort (Optional[Callable[[Listing], bool]]): Sorts the returned listings into the desired final order
                before returning.
            timeout_seconds (float): The max real time in seconds to try to get a listing before giving up. `-1`
                (default) indicates no timeout is required.
        """
        self._client = client
        self._api_param_iterator = search_request_iterator
        self._local_sort = local_sort
        self._end_time = (
            datetime.now() + timedelta(seconds=timeout_seconds)
            if timeout_seconds > 0
            else None
        )
        # We hold on to this to help with debugging. It's not used after generation.
        self._search_request: Optional[SearchListingsRequest] = None
        self._buffer: Optional[Iterable[Listing]] = None

    def __next__(self) -> Listing:
        """Gets the next listing from the buffer or fetches a new one if needed and available.

        This method enforces the timeout set at instantiation.
        """
        if self._end_time is not None:
            if datetime.now() > self._end_time:
                raise StopIteration("Timed out while searching listings")

        if self._buffer is None:
            self._buffer = self._refresh_buffer()

        while True:
            try:
                next_val = next(self._buffer)
                break
            except StopIteration:
                # This might throw a StopIteration also; that means we're actually done
                self._buffer = self._refresh_buffer()

        return next_val

    def __iter__(self):
        """Implements the iterable interface."""
        return self

    def _refresh_buffer(self):
        self._search_request = self._api_param_iterator.__next__()
        if self._local_sort is not None:
            result = sorted(
                self._client.search_listings(self._search_request).result,
                key=self._local_sort,
            )
        else:
            result = self._client.search_listings(self._search_request).result

        return iter(result)


_AGGRESSIVE_TARGETS = {
    "HR": Decimal("0.02"),
    "E": Decimal("0.26"),
    "D": Decimal("0.23"),
    "C": Decimal("0.22"),
    "B": Decimal("0.15"),
    "A": Decimal("0.06"),
    "AA": Decimal("0.06"),
}

_CONSERVATIVE_TARGETS = {
    "HR": Decimal("0.02"),
    "E": Decimal("0.06"),
    "D": Decimal("0.06"),
    "C": Decimal("0.15"),
    "B": Decimal("0.22"),
    "A": Decimal("0.26"),
    "AA": Decimal("0.23"),
}


class _BucketDatum(NamedTuple):
    value: Union[float, Decimal]
    pct_of_total: Union[float, Decimal]
    error_pct: Union[float, Decimal]


class FixedTargetAllocationStrategy(AllocationStrategy):
    """Defines an investment strategy where funds are allocated to different prosper ratings at a fixed rate."""

    def __init__(
        self,
        client: Client,
        targets: Dict[str, Decimal],
    ):
        """Instantiates a FixedTargetAllocationStrategy.

        Args:
            client (Client): The prosper API client.
            targets (Dict[str, Decimal]): The target allocations by prosper rating.
        """
        buckets = {}
        account = client.get_account_info()
        invested_notes = account.invested_notes.model_dump()
        pending_bids = account.pending_bids.model_dump()
        total_account_value = account.total_account_value
        for rating in invested_notes.keys():
            # This assumes the ratings will never change
            value = invested_notes[rating] + pending_bids[rating]
            pct_of_total = value / total_account_value
            buckets[rating] = _BucketDatum(
                value=value,
                pct_of_total=pct_of_total,
                error_pct=(targets[rating] if rating in targets else 0) - pct_of_total,
            )

        buckets["Cash"] = _BucketDatum(
            round_down_to_nearest_cent(account.available_cash_balance),
            account.available_cash_balance / total_account_value,
            0.0,
        )
        buckets["Pending deposit"] = _BucketDatum(
            account.pending_deposit,
            account.pending_deposit / total_account_value,
            0.0,
        )
        buckets["Total value"] = _BucketDatum(
            total_account_value, total_account_value / total_account_value, 0.0
        )

        logger.info(
            f"Pending investments = ${account.pending_investments_primary_market:8.2f}"
        )
        for key, bucket in buckets.items():
            logger.info(
                f"\t{key:17}= ${bucket.value:8.2f} ({bucket.pct_of_total * 100:6.2f}%) error: {bucket.error_pct * 100:6.3f}%"
            )

        grade_buckets_sorted_by_error_pct = sorted(
            (i for i in buckets.items() if i[0] in targets.keys()),
            key=lambda v: v[1].error_pct,
            reverse=True,
        )

        self._search_requests = [
            SearchListingsRequest(
                **{**_BASE_REQUEST.model_dump(), "prosper_rating": [b[0]]},
            )
            for b in grade_buckets_sorted_by_error_pct
        ]

        super().__init__(client, iter(self._search_requests))


class HighestMatchingRateAllocationStrategy(AllocationStrategy):
    """Allocation strategy that greedily takes the listing with the highest lender yield."""

    def __init__(self, client: Client, request: SearchListingsRequest):
        """Creates a new allocation strategy.

        Args:
            client (Client): Prosper client
            request (SearchListingsRequest): Base request for searching
        """
        self._search_requests = [request]
        super().__init__(client, iter(self._search_requests))


class AllocationStrategies(Enum):
    """Enumerates the pre-configured targets for AllocationStrategy."""

    AGGRESSIVE = (
        FixedTargetAllocationStrategy,
        _AGGRESSIVE_TARGETS,
    )
    CONSERVATIVE = (
        FixedTargetAllocationStrategy,
        _CONSERVATIVE_TARGETS,
    )
    OVERALL_HIGHEST_RATE = (
        HighestMatchingRateAllocationStrategy,
        _BASE_REQUEST,
    )

    def __str__(self):
        """Return the name of the enum to make it more palatable in the CLI help."""
        return self.name

    def to_strategy(self, client: Client) -> AllocationStrategy:
        """Converts the enum into a strategy, given a client and an account.

        Args:
            client (Client): Prosper client

        Returns:
            AllocationStrategy: Allocation strategy matching the inputs.
        """
        cls = self.value[0]
        args = self.value[1:]

        return cls(client, *args)
