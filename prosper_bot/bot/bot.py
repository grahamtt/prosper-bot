import logging
from datetime import timedelta
from decimal import Decimal
from time import sleep
from typing import Union

import humanize
import simplejson as json
from prosper_api.client import Client
from prosper_shared.omni_config import ConfigKey, config_schema
from schema import Optional as SchemaOptional

from prosper_bot.allocation_strategy import AllocationStrategies
from prosper_bot.cli import DRY_RUN_CONFIG, VERBOSE_CONFIG, build_config
from prosper_bot.util import round_down_to_nearest_cent

logger = logging.getLogger(__file__)

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO
)

MIN_BID_CONFIG = "prosper-bot.bot.min_bid"
TARGET_LOAN_COUNT_CONFIG = "prosper-bot.bot.target-loan-count"
STRATEGY_CONFIG = "prosper-bot.bot.strategy"

POLL_TIME = timedelta(minutes=1)
MIN_ALLOWED_BID = Decimal("25.00")


@config_schema
def _schema():
    return {
        "prosper-bot": {
            "bot": {
                ConfigKey(
                    "min-bid",
                    "Minimum amount of a loan to purchase.",
                    default=MIN_ALLOWED_BID,
                ): Decimal,
                ConfigKey(
                    "strategy",
                    "Strategy for balancing your portfolio.",
                    default=AllocationStrategies.AGGRESSIVE,
                ): AllocationStrategies,
                SchemaOptional(
                    ConfigKey(
                        "target-loan-count",
                        "Calculate min bid based on (total account value / target loan count). Overrides min-bid if present.",
                    )
                ): int,
            }
        }
    }


class Bot:
    """Prosper trading bot."""

    strategy: AllocationStrategies

    def __init__(self, config=None):
        """Initializes the bot with the given argument values."""
        if config is None:
            config = build_config()
        self.config = config
        if self.config.get_as_bool(VERBOSE_CONFIG):
            logging.root.setLevel(logging.DEBUG)
            logger.setLevel(logging.DEBUG)

        self.client = Client(config=self.config)
        self.dry_run = self.config.get_as_bool(DRY_RUN_CONFIG)
        self.min_bid = self.config.get_as_decimal(MIN_BID_CONFIG, Decimal(25.00))
        self.target_loan_count = self.config.get(TARGET_LOAN_COUNT_CONFIG)
        self.strategy = self.config.get_as_enum(STRATEGY_CONFIG, AllocationStrategies)

    def run(self):
        """Main loop for the trading bot."""
        sleep_time_delta = POLL_TIME
        cash = None
        while True:
            try:
                cash, sleep_time_delta = self._do_run(cash)
            except KeyboardInterrupt:
                logger.info("Interrupted...")
                break
            except Exception as e:
                logger.warning(
                    f"Caught exception running bot loop: {e}. Continuing after {humanize.naturaldelta(sleep_time_delta)}..."
                )
                logger.debug("", exc_info=e)

            sleep(sleep_time_delta.total_seconds())

    def _do_run(self, previous_cash):
        account = self.client.get_account_info()
        logger.debug(json.dumps(account, indent=2, default=str))

        cash = account.available_cash_balance
        if previous_cash == cash:
            return cash, POLL_TIME

        allocation_strategy = self.strategy.to_strategy(self.client)

        invest_amount = self._get_bid_amount(
            cash, self.min_bid, account.total_account_value, self.target_loan_count
        )
        if invest_amount or self.dry_run:
            logger.info("Enough cash is available; searching for loans...")

            listing = next(allocation_strategy)
            lender_yield = listing.lender_yield
            listing_number = listing.listing_number
            if self.dry_run:
                logger.info(
                    f"DRYRUN: Would have purchased ${invest_amount:5.2f} of listing {listing_number} ({listing.prosper_rating}) at {lender_yield * 100:5.2f}% for {listing.listing_term} months"
                )
            else:
                order_result = self.client.order(listing_number, invest_amount)
                logging.info(
                    f"Purchased ${invest_amount:5.2f} of {listing_number} ({listing.prosper_rating}) at {lender_yield * 100:5.2f}% for {listing.listing_term} months"
                )
                logging.debug(json.dumps(order_result, indent=2, default=str))

            # Set the sleep time here in case of no matching listings being found (highly unlikely).
            sleep_time_delta = timedelta(seconds=5)
        else:
            sleep_time_delta = POLL_TIME
            logger.info(f"Starting polling once {humanize.naturaldelta(POLL_TIME)}...")

        return cash, sleep_time_delta

    @staticmethod
    def _get_bid_amount(
        cash: Decimal,
        min_bid: Decimal,
        total_account_value,
        target_loan_count: Union[int, None],
    ):
        if target_loan_count is not None:
            min_bid = max(
                round_down_to_nearest_cent(total_account_value / target_loan_count),
                MIN_ALLOWED_BID,
            )

        logger.debug(f"Using ${min_bid} for min bid size")

        if cash < min_bid:
            return 0
        return round_down_to_nearest_cent(min_bid + cash % min_bid)


def runner():
    """Entry-point for Python script."""
    Bot().run()


if __name__ == "__main__":
    Bot().run()
