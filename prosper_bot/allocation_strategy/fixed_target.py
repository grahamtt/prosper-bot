from decimal import Decimal
from enum import Enum
from logging import getLogger
from typing import NamedTuple, Union

from prosper_api.client import Client
from prosper_api.models import Account, SearchListingsRequest

from prosper_bot.allocation_strategy import AllocationStrategy

logger = getLogger(__file__)

_AGGRESSIVE_TARGETS = {
    "NA": Decimal("0"),
    "HR": Decimal("0.02"),
    "E": Decimal("0.26"),
    "D": Decimal("0.23"),
    "C": Decimal("0.22"),
    "B": Decimal("0.15"),
    "A": Decimal("0.06"),
    "AA": Decimal("0.06"),
}

_CONSERVATIVE_TARGETS = {
    "NA": Decimal("0"),
    "HR": Decimal("0.02"),
    "E": Decimal("0.06"),
    "D": Decimal("0.06"),
    "C": Decimal("0.15"),
    "B": Decimal("0.22"),
    "A": Decimal("0.26"),
    "AA": Decimal("0.23"),
}


class FixedTargetAllocationStrategyTargets(Enum):
    """Enumerates the pre-configured targets for FixedTargetAllocationStrategy."""

    AGGRESSIVE = _AGGRESSIVE_TARGETS
    CONSERVATIVE = _CONSERVATIVE_TARGETS


class _BucketDatum(NamedTuple):
    value: Union[float, Decimal]
    pct_of_total: Union[float, Decimal]
    error_pct: Union[float, Decimal]


class FixedTargetAllocationStrategy(AllocationStrategy):
    """Defines an investment strategy where funds are allocated to different prosper ratings at a fixed rate."""

    def __init__(
        self,
        client: Client,
        account: Account,
        targets: FixedTargetAllocationStrategyTargets = None,
    ):
        """Instantiates a FixedTargetAllocationStrategy.

        Args:
            client (Client): The prosper API client.
            account (Account): Represents the current status of the Prosper account.
            targets (FixedTargetAllocationStrategyTargets): The target allocations by prosper rating.
        """
        if targets is None:
            targets = FixedTargetAllocationStrategyTargets.AGGRESSIVE
        targets_dict = targets.value
        buckets = {}
        invested_notes = account.invested_notes._asdict()
        pending_bids = account.pending_bids._asdict()
        total_account_value = account.total_account_value
        for rating in invested_notes.keys():
            # This assumes the ratings will never change
            value = invested_notes[rating] + pending_bids[rating]
            pct_of_total = value / total_account_value
            buckets[rating] = _BucketDatum(
                value=value,
                pct_of_total=pct_of_total,
                error_pct=targets_dict[rating] - pct_of_total,
            )

        buckets["Cash"] = _BucketDatum(
            account.available_cash_balance,
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
            f"Pending investments = ${account.pending_investments_primary_market:7.2f}"
        )
        for key, bucket in buckets.items():
            logger.info(
                f"\t{key:16}= ${bucket.value:8.2f} ({bucket.pct_of_total * 100:6.2f}%) error: {bucket.error_pct * 100:6.3f}%"
            )

        grade_buckets_sorted_by_error_pct = sorted(
            buckets.items(), key=lambda v: v[1].error_pct, reverse=True
        )

        self._search_requests = [
            SearchListingsRequest(
                limit=10,
                biddable=True,
                invested=False,
                prosper_rating=[b[0]],
                sort_by="lender_yield",
                sort_dir="desc",
            )
            for b in grade_buckets_sorted_by_error_pct
        ]

        super().__init__(client, iter(self._search_requests))
