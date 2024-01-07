import datetime
from datetime import timedelta
from decimal import Decimal
from os.path import join
from tempfile import TemporaryDirectory

import pytest
from prosper_api.models import Account, Listing, Order
from prosper_shared.omni_config import Config
from prosper_shared.serde import Serde
from simplejson import dumps

from prosper_bot.allocation_strategy import AllocationStrategies
from prosper_bot.bot import bot
from prosper_bot.bot.bot import Bot
from prosper_bot.cli import DRY_RUN_CONFIG


class TestBot:
    @pytest.fixture
    def client_mock(self, mocker):
        return mocker.patch("prosper_bot.bot.bot.Client")

    @pytest.mark.parametrize(
        ["input", "min_bid", "expected_output"],
        [
            # Min bid = 25
            (Decimal("0"), Decimal("25"), Decimal("0")),
            (Decimal("24.99"), Decimal("25"), Decimal("0")),
            (Decimal("25.00"), Decimal("25"), Decimal("25.00")),
            (Decimal("25.01"), Decimal("25"), Decimal("25.01")),
            (Decimal("49.99"), Decimal("25"), Decimal("49.99")),
            (Decimal("50.00"), Decimal("25"), Decimal("25.00")),
            (Decimal("50.01"), Decimal("25"), Decimal("25.01")),
            # Min bid = 30
            (Decimal("50.00"), Decimal("30"), Decimal("50.00")),
            (Decimal("59.99"), Decimal("30"), Decimal("59.99")),
            (Decimal("60.00"), Decimal("30"), Decimal("30.00")),
            (Decimal("60.01"), Decimal("30"), Decimal("30.01")),
            (Decimal("55.11"), Decimal("27.56"), Decimal("55.11")),
            (Decimal("55.12"), Decimal("27.56"), Decimal("27.56")),
            (Decimal("55.13"), Decimal("27.56"), Decimal("27.57")),
        ],
    )
    def test__get_bid_amount(self, input: Decimal, min_bid: Decimal, expected_output):
        assert Bot._get_bid_amount(input, min_bid) == expected_output

    @pytest.mark.timeout("5")
    def test_run_when_exception(self, mocker, client_mock):
        botty = Bot(Config({}))
        do_run_mock = mocker.spy(botty, "_do_run")
        mocker.patch.object(bot, "POLL_TIME", timedelta(milliseconds=10))
        do_run_mock.side_effect = [
            Exception("Should be caught"),
            KeyboardInterrupt("This should do it"),
        ]

        botty.run()

        do_run_mock.assert_has_calls([mocker.call(), mocker.call()])

    @pytest.mark.parametrize(
        ["cli_config", "bot_config", "available_cash", "expected_order_amount"],
        [
            ({}, {}, Decimal("111.1111"), Decimal("36.1111")),
            ({}, {}, Decimal("24.99"), None),
            ({"dry-run": True}, {}, Decimal("24.99"), None),
        ],
    )
    def test_do_run(
        self,
        mocker,
        client_mock,
        cli_config,
        bot_config,
        available_cash,
        expected_order_amount,
    ):
        config = Config(
            {
                "prosper-shared": {"serde": {"use-decimals": True}},
                "prosper-bot": {"cli": cli_config, "bot": bot_config},
            }
        )
        config.get_as_enum = mocker.MagicMock()
        config.get_as_enum.return_value = AllocationStrategies.AGGRESSIVE
        dry_run = config.get_as_bool(DRY_RUN_CONFIG, False)
        serde = Serde(config)
        strategy_mock = mocker.MagicMock()
        AllocationStrategies.AGGRESSIVE.to_strategy = strategy_mock
        strategy_mock.return_value.__next__.return_value = serde.deserialize(
            dumps(
                {
                    "credit_bureau_values_transunion_indexed": {
                        "g102s_months_since_most_recent_inquiry": -4.0,
                        "credit_report_date": "2023-08-28 17:35:20 +0000",
                        "at02s_open_accounts": 6.0,
                        "g041s_accounts_30_or_more_days_past_due_ever": 0.0,
                        "g093s_number_of_public_records": 0.0,
                        "g094s_number_of_public_record_bankruptcies": -4.0,
                        "g095s_months_since_most_recent_public_record": -4.0,
                        "g218b_number_of_delinquent_accounts": 0.0,
                        "g980s_inquiries_in_the_last_6_months": -4.0,
                        "re20s_age_of_oldest_revolving_account_in_months": 142.0,
                        "s207s_months_since_most_recent_public_record_bankruptcy": -4.0,
                        "re33s_balance_owed_on_all_revolving_accounts": 6565.0,
                        "at57s_amount_delinquent": 0.0,
                        "g099s_public_records_last_24_months": -4.0,
                        "at20s_oldest_trade_open_date": 189.0,
                        "at03s_current_credit_lines": 6.0,
                        "re101s_revolving_balance": 6565.0,
                        "bc34s_bankcard_utilization": 17.0,
                        "at01s_credit_lines": 28.0,
                        "fico_score": "780-799",
                    },
                    "listing_number": 11111111,
                    "listing_start_date": "2023-08-28 22:00:47 +0000",
                    "historical_return": 0.04485,
                    "historical_return_10th_pctl": 0.03404,
                    "historical_return_90th_pctl": 0.05707,
                    "employment_status_description": "Employed",
                    "occupation": "Nurse (RN)",
                    "has_mortgage": True,
                    "co_borrower_application": False,
                    "investment_type_description": "Fractional",
                    "last_updated_date": "2023-08-29 14:33:41 +0000",
                    "invested": True,
                    "biddable": False,
                    "lender_yield": 0.1295,
                    "borrower_rate": 0.1395,
                    "borrower_apr": 0.1677,
                    "listing_term": 48,
                    "listing_monthly_payment": 273.01,
                    "prosper_score": 11,
                    "listing_category_id": 7,
                    "listing_title": "Other",
                    "income_range": 6,
                    "income_range_description": "$100,000+",
                    "stated_monthly_income": 8333.33,
                    "income_verifiable": True,
                    "dti_wprosper_loan": 0.2478,
                    "borrower_state": "AL",
                    "prior_prosper_loans_active": 0,
                    "prior_prosper_loans": 0,
                    "prior_prosper_loans_late_cycles": 0,
                    "prior_prosper_loans_late_payments_one_month_plus": 0,
                    "lender_indicator": 0,
                    "channel_code": "40000",
                    "amount_participation": 0.0,
                    "investment_typeid": 1,
                    "loan_number": 2119830,
                    "months_employed": 46.0,
                    "investment_product_id": 1,
                    "decision_bureau": "TransUnion",
                    "member_key": "AAAAAAAAAAAAAAAAAAAAAAAAA",
                    "listing_end_date": "2023-08-29 14:33:31 +0000",
                    "listing_creation_date": "2023-08-28 17:42:57 +0000",
                    "loan_origination_date": "2023-08-30 07:00:00 +0000",
                    "listing_status": 6,
                    "listing_status_reason": "Completed",
                    "listing_amount": 10000.0,
                    "amount_funded": 10000.0,
                    "amount_remaining": 0.0,
                    "percent_funded": 1.0,
                    "partial_funding_indicator": True,
                    "funding_threshold": 0.7,
                    "prosper_rating": "AA",
                }
            ),
            Listing,
        )

        client_mock.return_value.get_account_info.return_value = serde.deserialize(
            dumps(
                {
                    "available_cash_balance": available_cash,
                    "pending_investments_primary_market": 0.0,
                    "pending_investments_secondary_market": 0.0,
                    "pending_quick_invest_orders": 0.0,
                    "total_principal_received_on_active_notes": 111.11,
                    "total_amount_invested_on_active_notes": 1111.11,
                    "outstanding_principal_on_active_notes": 1111.11,
                    "total_account_value": 1111.11,
                    "pending_deposit": 0.0,
                    "last_deposit_amount": 30.0,
                    "last_deposit_date": "2023-10-23 07:00:00 +0000",
                    "last_withdraw_amount": -14.31,
                    "last_withdraw_date": "2012-11-07 08:00:00 +0000",
                    "external_user_id": "AAAAAAAAA-0000-AAAA-AAAA-AAAAAAAA",
                    "prosper_account_digest": "Aa=",
                    "invested_notes": {
                        "NA": 0,
                        "HR": 11.080180,
                        "E": 1111.056157,
                        "D": 111.837770,
                        "C": 111.719430,
                        "B": 111.842790,
                        "A": 111.991266,
                        "AA": 111.641243,
                    },
                    "pending_bids": {
                        "NA": 0,
                        "HR": 0,
                        "E": 0,
                        "D": 0,
                        "C": 0,
                        "B": 0,
                        "A": 0,
                        "AA": 0,
                    },
                }
            ),
            Account,
        )
        client_mock.return_value.order.return_value = serde.deserialize(
            dumps(
                {
                    "order_id": "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAA",
                    "bid_requests": [
                        {
                            "listing_id": 11111111,
                            "bid_amount": 25.0,
                            "bid_status": "PENDING",
                        }
                    ],
                    "order_status": "IN_PROGRESS",
                    "source": "AI",
                    "order_date": "2023-09-18 16:08:23 +0000",
                }
            ),
            Order,
        )

        botty = Bot(config)
        sleep_time = botty._do_run()

        client_mock.return_value.get_account_info.assert_called_once()
        if available_cash > Decimal("25") or dry_run:
            strategy_mock.return_value.__next__.assert_called_once()
            assert sleep_time == datetime.timedelta(seconds=5)
        else:
            strategy_mock.return_value.__next__.assert_not_called()
            assert sleep_time == datetime.timedelta(seconds=60)
        if expected_order_amount:
            client_mock.return_value.order.assert_called_once_with(
                11111111, expected_order_amount
            )
        else:
            client_mock.return_value.order.assert_not_called()

    def test_init_when_config_is_none(self, mocker):
        build_config_mock = mocker.patch("prosper_bot.bot.bot.build_config")
        with TemporaryDirectory() as tmpdir:
            build_config_mock.return_value.get_as_str.return_value = join(
                tmpdir, "token_cache"
            )
            botty = Bot()

        assert botty.config == build_config_mock.return_value
