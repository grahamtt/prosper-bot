import json
import logging
from datetime import datetime, timedelta, tzinfo
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
                f"\tNA = ${na_value} ({na_value / total_account_value}%) error: 0%\n"
                f'\tHR = ${hr_value} ({hr_value / total_account_value}%) error: {error_vals["HR"]}\n'
                f'\tE = ${e_value} ({e_value / total_account_value}%) error: {error_vals["E"]}\n'
                f'\tD = ${d_value} ({d_value / total_account_value}%) error: {error_vals["D"]}\n'
                f'\tC = ${c_value} ({c_value / total_account_value}%) error: {error_vals["C"]}\n'
                f'\tB = ${b_value} ({b_value / total_account_value}%) error: {error_vals["B"]}\n'
                f'\tA = ${a_value} ({a_value / total_account_value}%) error: {error_vals["A"]}\n'
                f'\tAA = ${aa_value} ({aa_value / total_account_value}% error: {error_vals["AA"]}\n'
                f"\tCash = ${cash} ({cash / total_account_value}%)"
            )

            if cash >= 25:
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

                invest_amount = (cash // 25) * 25 + cash % 25
                order_result = self.client.order(
                    listings["result"][0]["listing_number"], invest_amount
                )
                logging.info(json.dumps(order_result, indent=2))
                sleep_time = 60  # seconds

            else:
                logger.info("Not enough cash available")
                sleep_time = (
                    (
                        datetime.now(pytz.timezone("America/Denver"))
                        + timedelta(days=1)
                    ).replace(hour=7, minute=0, second=0, microsecond=0)
                    - datetime.now(pytz.timezone("America/Denver"))
                ).total_seconds()

            logger.info(f"Sleeping for {sleep_time} seconds")
            sleep(sleep_time)

            # notes = client.list_notes(limit=100)
            # logger.info(json.dumps(notes, indent=2))
            #
            # listing = client.search_listings(listing_number=["13201299"], invested=True, biddable=False)
            # logger.info(json.dumps(listing, indent=2))


if __name__ == "__main__":
    Bot().run()
