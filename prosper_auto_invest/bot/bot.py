import argparse
import json
import logging
from datetime import datetime, timedelta, tzinfo

from humanize import naturaldelta
from time import sleep

import pytz
import requests

from prosper_api.auth_token_manager import AuthTokenManager
from prosper_api.client import Client
from prosper_api.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


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
            total_account_value = account["total_account_value"]
            na_value = account["invested_notes"]["NA"] + account["pending_bids"]["NA"]
            hr_value = account["invested_notes"]["HR"] + account["pending_bids"]["HR"]
            e_value = account["invested_notes"]["E"] + account["pending_bids"]["E"]
            d_value = account["invested_notes"]["D"] + account["pending_bids"]["D"]
            c_value = account["invested_notes"]["C"] + account["pending_bids"]["C"]
            b_value = account["invested_notes"]["B"] + account["pending_bids"]["B"]
            a_value = account["invested_notes"]["A"] + account["pending_bids"]["A"]
            aa_value = account["invested_notes"]["AA"] + account["pending_bids"]["AA"]
            cash = account["available_cash_balance"]
            targets = {
                "HR": 0.02,
                "E": 0.26,
                "D": 0.23,
                "C": 0.22,
                "B": 0.15,
                "A": 0.06,
                "AA": 0.06,
            }
            error_vals = {
                "HR": targets["HR"] - hr_value / total_account_value,
                "E": targets["E"] - e_value / total_account_value,
                "D": targets["D"] - d_value / total_account_value,
                "C": targets["C"] - c_value / total_account_value,
                "B": targets["B"] - b_value / total_account_value,
                "A": targets["A"] - a_value / total_account_value,
                "AA": targets["AA"] - aa_value / total_account_value,
            }
            errors_by_magnitude = sorted(
                error_vals.items(), key=lambda v: v[1], reverse=True
            )
            logger.info(
                f"Total value = ${total_account_value}\n"
                # f"In-flight payments = ${account['inflight_gross']}\n"
                f"Pending investments = ${account['pending_investments_primary_market']:7.2f}\n"
                f"\tNA\t\t\t\t= ${na_value:7.2f} ({na_value / total_account_value * 100:4.2f}%) error: 0%\n"
                f'\tHR\t\t\t\t= ${hr_value:7.2f} ({hr_value / total_account_value * 100:4.2f}%) error: {error_vals["HR"] * 100:5.4f}%\n'
                f'\tE\t\t\t\t= ${e_value:7.2f} ({e_value / total_account_value * 100:4.2f}%) error: {error_vals["E"] * 100:5.4f}%\n'
                f'\tD\t\t\t\t= ${d_value:7.2f} ({d_value / total_account_value * 100:4.2f}%) error: {error_vals["D"] * 100:5.4f}%\n'
                f'\tC\t\t\t\t= ${c_value:7.2f} ({c_value / total_account_value * 100:4.2f}%) error: {error_vals["C"] * 100:5.4f}%\n'
                f'\tB\t\t\t\t= ${b_value:7.2f} ({b_value / total_account_value * 100:4.2f}%) error: {error_vals["B"] * 100:5.4f}%\n'
                f'\tA\t\t\t\t= ${a_value:7.2f} ({a_value / total_account_value * 100:4.2f}%) error: {error_vals["A"] * 100:5.4f}%\n'
                f'\tAA\t\t\t\t= ${aa_value:7.2f} ({aa_value / total_account_value * 100:4.2f}%) error: {error_vals["AA"] * 100:5.4f}%\n'
                f"\tCash\t\t\t= ${cash:7.2f} ({cash / total_account_value * 100:4.2f}%)\n"
                f"\tPending deposit = ${account['pending_deposit']} ({account['pending_deposit']/total_account_value * 100:4.2f}%)"
            )

            if cash >= 25 or self.args.dry_run:
                target_grade = errors_by_magnitude[0][0]
                logger.info(
                    f"Enough cash available; lets buy something in grade {target_grade}"
                )

                listings = self.client.search_listings(
                    limit=500,
                    prosper_rating=[target_grade],
                    sort_by="lender_yield",
                    sort_dir="desc",
                )
                # listings['result'].sort(key=lambda v: v['historical_return'], reverse=True)
                logger.info(json.dumps(listings["result"][0], indent=2))

                invest_amount = 25 + cash % 25
                listing_number = listings["result"][0]["listing_number"]
                if self.args.dry_run:
                    logger.info(
                        f"DRYRUN: Would have purchased ${invest_amount} of listing {listing_number}"
                    )
                else:
                    order_result = self.client.order(listing_number, invest_amount)
                    logging.info(json.dumps(order_result, indent=2))
                sleep_time_delta = timedelta(seconds=60)

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
