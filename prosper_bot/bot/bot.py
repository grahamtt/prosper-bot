import logging
from collections import namedtuple
from datetime import timedelta
from decimal import ROUND_DOWN, Decimal
from time import sleep

import simplejson as json
from humanize import naturaldelta
from prosper_api.client import Client
from prosper_api.config import Config
from prosper_api.models import SearchListingsRequest

from prosper_bot.cli import build_config

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO
)
logger = logging.getLogger(__file__)

DRY_RUN_CONFIG = "bot.dry_run"
VERBOSE_CONFIG = "bot.verbose"
MIN_BID_CONFIG = "bot.min_bid"

POLL_TIME = timedelta(minutes=1)
TARGETS = {
    "NA": Decimal("0"),
    "HR": Decimal("0.02"),
    "E": Decimal("0.26"),
    "D": Decimal("0.23"),
    "C": Decimal("0.22"),
    "B": Decimal("0.15"),
    "A": Decimal("0.06"),
    "AA": Decimal("0.06"),
}

BucketDatum = namedtuple("BucketDatum", ["value", "pct_of_total", "error_pct"])


class Bot:
    """Prosper trading bot."""

    def __init__(self):
        """Initializes the bot with the given argument values."""
        self.config = Config(config_dict=build_config())
        if self.config.get_as_bool(VERBOSE_CONFIG):
            logger.setLevel(logging.DEBUG)

        self.client = Client(config=self.config)
        self.dry_run = self.config.get_as_bool(DRY_RUN_CONFIG)
        self.min_bid = self.config.get_as_decimal(MIN_BID_CONFIG, Decimal(25.00))

    def run(self):
        """Main loop for the trading bot."""
        cash = None
        while True:
            cash, sleep_time_delta = self._do_run(cash)

            sleep(sleep_time_delta.total_seconds())

    def _do_run(self, cash):
        account = self.client.get_account_info()
        logger.debug(json.dumps(account, indent=2, default=str))
        new_cash = _to_dollars(account.available_cash_balance)
        if cash == new_cash:
            return cash, POLL_TIME
        total_account_value = _to_dollars(account.total_account_value)
        buckets = {}
        invested_notes = account.invested_notes._asdict()
        pending_bids = account.pending_bids._asdict()
        for rating in invested_notes.keys():
            value = _to_dollars(invested_notes[rating] + pending_bids[rating])
            pct_of_total = value / total_account_value
            buckets[rating] = BucketDatum(
                value=value,
                pct_of_total=pct_of_total,
                error_pct=TARGETS[rating] - pct_of_total,
            )

        grade_buckets_sorted_by_error_pct = sorted(
            buckets.items(), key=lambda v: v[1].error_pct, reverse=True
        )

        cash = new_cash
        buckets["Cash"] = BucketDatum(
            cash,
            cash / total_account_value,
            0.0,
        )
        buckets["Pending deposit"] = BucketDatum(
            _to_dollars(account.pending_deposit),
            _to_dollars(account.pending_deposit) / total_account_value,
            0.0,
        )
        buckets["Total value"] = BucketDatum(
            total_account_value, total_account_value / total_account_value, 0.0
        )

        logger.info(
            f"Pending investments = ${account.pending_investments_primary_market:7.2f}"
        )
        for key, bucket in buckets.items():
            logger.info(
                f"\t{key:16}= ${bucket.value:8.2f} ({bucket.pct_of_total * 100:6.2f}%) error: {bucket.error_pct * 100:6.3f}%"
            )

        invest_amount = self._get_bid_amount(cash, self.min_bid)
        if invest_amount or self.dry_run:
            logger.info("Enough cash is available; searching for loans...")
            for target_grade, bucket in grade_buckets_sorted_by_error_pct:
                logger.info(f"Searching for something in grade {target_grade}...")

                listings = self.client.search_listings(
                    SearchListingsRequest(
                        limit=10,
                        biddable=True,
                        invested=False,
                        prosper_rating=[target_grade],
                        sort_by="lender_yield",
                        sort_dir="desc",
                    )
                )

                if listings.result_count == 0:
                    logger.info(f"No matching listings found for grade {target_grade}")
                    continue

                listing = listings.result[0]
                logger.debug(json.dumps(listing, indent=2, default=str))

                lender_yield = listing.lender_yield
                listing_number = listing.listing_number
                if self.dry_run:
                    logger.info(
                        f"DRYRUN: Would have purchased ${invest_amount:5.2f} of listing {listing_number} at {lender_yield * 100:5.2f}%"
                    )
                else:
                    order_result = self.client.order(listing_number, invest_amount)
                    logging.info(
                        f"Purchased ${invest_amount:5.2f} of {listing_number} at {lender_yield * 100:5.2f}%"
                    )
                    logging.debug(json.dumps(order_result, indent=2, default=str))
                break
            # Set the sleep time here in case of no matching listings being found (highly unlikely).
            sleep_time_delta = timedelta(seconds=5)
        else:
            sleep_time_delta = POLL_TIME
            logger.info(f"Starting polling every {naturaldelta(sleep_time_delta)}")

        return cash, sleep_time_delta

    @staticmethod
    def _get_bid_amount(cash, min_bid):
        if cash < min_bid:
            return 0
        return min_bid + cash % min_bid


def _to_dollars(val: float) -> Decimal:
    return Decimal(val).quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def runner():
    """Entry-point for Python script."""
    Bot().run()


if __name__ == "__main__":
    Bot().run()
