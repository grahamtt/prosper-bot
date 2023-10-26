import argparse
import json
import logging
from collections import namedtuple
from datetime import datetime, timedelta, tzinfo

from humanize import naturaldelta
from time import sleep

import pytz
import requests

from prosper_api.auth_token_manager import AuthTokenManager
from prosper_api.client import Client
from prosper_api.config import Config
from prosper_api.models import AmountsByRating

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

TARGETS = {
    "NA": 0,
    "HR": 0.02,
    "E": 0.26,
    "D": 0.23,
    "C": 0.22,
    "B": 0.15,
    "A": 0.06,
    "AA": 0.06,
}

BucketDatum = namedtuple("BucketDatum", ["value", "pct_of_total", "error_pct"])


class Bot:
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog="Prosper auto-invest",
            description="A bot that can find and invest in loans",
        )
        parser.add_argument(
            "-d",
            "--dry-run",
            help="Do everything but actually purchase the loans",
            action="store_true",
        )
        self.args = parser.parse_args()

        self.client = Client()

    def run(self):
        while True:
            account = self.client.get_account_info()
            logger.debug(json.dumps(account, indent=2))
            total_account_value = account.total_account_value
            buckets = {}
            invested_notes = account.invested_notes._asdict()
            pending_bids = account.pending_bids._asdict()
            for rating in invested_notes.keys():
                value = invested_notes[rating] + pending_bids[rating]
                pct_of_total = value / total_account_value
                buckets[rating] = BucketDatum(
                    value=value,
                    pct_of_total=pct_of_total,
                    error_pct=TARGETS[rating] - pct_of_total,
                )

            buckets["Cash"] = BucketDatum(
                account.available_cash_balance,
                account.available_cash_balance / total_account_value,
                0.0,
            )
            buckets["Pending deposit"] = BucketDatum(
                account.pending_deposit,
                account.pending_deposit / total_account_value,
                0.0,
            )
            buckets["Total value"] = BucketDatum(
                total_account_value, total_account_value / total_account_value, 0.0
            )

            cash = account.available_cash_balance
            grade_buckets_sorted_by_error_pct = sorted(
                buckets.items(), key=lambda v: v[1].error_pct, reverse=True
            )
            logger.info(f"Total value = ${total_account_value}")
            logger.info(
                f"Pending investments = ${account.pending_investments_primary_market:7.2f}"
            )
            for key, bucket in buckets.items():
                logger.info(
                    f"\t{key:16}= ${bucket.value:8.2f} ({bucket.pct_of_total * 100:6.2f}%) error: {bucket.error_pct*100:6.3f}%"
                )

            if cash >= 25 or self.args.dry_run:
                for target_grade, bucket in grade_buckets_sorted_by_error_pct:
                    logger.info(
                        f"Enough cash available; searching for something in {target_grade}"
                    )

                    listings = self.client.search_listings(
                        limit=500,
                        prosper_rating=[target_grade],
                        sort_by="lender_yield",
                        sort_dir="desc",
                    )

                    if not listings["result"]:
                        logger.info("No matching listings found")
                        continue
                    # listings['result'].sort(key=lambda v: v['historical_return'], reverse=True)
                    listing = listings["result"][0]
                    logger.debug(json.dumps(listing, indent=2))

                    invest_amount = 25 + cash % 25
                    lender_yield = listing["lender_yield"]
                    listing_number = listing["listing_number"]
                    if self.args.dry_run:
                        logger.info(
                            f"DRYRUN: Would have purchased ${invest_amount:5.2f} of listing {listing_number} at {lender_yield * 100:5.2f}%"
                        )
                    else:
                        order_result = self.client.order(listing_number, invest_amount)
                        logging.info(
                            f"Purchased ${invest_amount:5.2f} of {listing_number} at {lender_yield * 100:5.2f}%"
                        )
                        logging.debug(json.dumps(order_result, indent=2))
                    sleep_time_delta = timedelta(seconds=60)
                    break

            else:
                logger.info("Not enough cash available")
                now = datetime.now(pytz.timezone("America/Denver"))
                sleep_time_delta = (now + timedelta(days=1)).replace(
                    hour=7, minute=0, second=0, microsecond=0
                ) - now

            logger.info(f"Sleeping for {naturaldelta(sleep_time_delta)}")
            sleep(sleep_time_delta.total_seconds())

            # notes = client.list_notes(limit=100)
            # logger.info(json.dumps(notes, indent=2))
            #
            # listing = client.search_listings(listing_number=["13201299"], invested=True, biddable=False)
            # logger.info(json.dumps(listing, indent=2))


if __name__ == "__main__":
    Bot().run()
