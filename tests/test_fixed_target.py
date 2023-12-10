import datetime
from decimal import Decimal

import pytest
from prosper_api.client import Client
from prosper_api.models import Account, AmountsByRating

from prosper_bot.allocation_strategy.fixed_target import FixedTargetAllocationStrategy


class TestFixedTarget:
    TEST_ACCOUNT = Account(
        available_cash_balance=Decimal("0.000558"),
        pending_investments_primary_market=Decimal("50.17"),
        pending_investments_secondary_market=Decimal("0.0"),
        pending_quick_invest_orders=Decimal("0.0"),
        total_principal_received_on_active_notes=Decimal("458.01"),
        total_amount_invested_on_active_notes=Decimal("6059.63"),
        outstanding_principal_on_active_notes=Decimal("5601.621111"),
        total_account_value=Decimal("5651.791111"),
        pending_deposit=Decimal("0.0"),
        last_deposit_amount=Decimal("222.0"),
        last_deposit_date=datetime.datetime(
            2023, 12, 4, 8, 0, tzinfo=datetime.timezone.utc
        ),
        last_withdraw_amount=Decimal("-14.31"),
        last_withdraw_date=datetime.datetime(
            2012, 11, 7, 8, 0, tzinfo=datetime.timezone.utc
        ),
        external_user_id="ABCDEFG1234567890",
        prosper_account_digest="0123456789ABCDEF=",
        invested_notes=AmountsByRating(
            NA=0,
            HR=Decimal("116.481738"),
            E=Decimal("1421.386003"),
            D=Decimal("1240.386786"),
            C=Decimal("1238.236872"),
            B=Decimal("856.850733"),
            A=Decimal("360.112822"),
            AA=Decimal("357.569852"),
        ),
        pending_bids=AmountsByRating(
            NA=0, HR=0, E=Decimal("25.0000"), D=Decimal("25.1700"), C=0, B=0, A=0, AA=0
        ),
    )

    @pytest.fixture
    def mock_client(self, mocker) -> Client:
        return mocker.patch("prosper_bot.allocation_strategy.fixed_target.Client")

    def test_fixed_target_allocation_strategy(self, mock_client):
        allocation_strategy = FixedTargetAllocationStrategy(
            mock_client, self.TEST_ACCOUNT
        )

        assert [r.prosper_rating for r in allocation_strategy._search_requests] == [
            ["D"],
            ["E"],
            ["C"],
            ["NA"],
            ["Cash"],
            ["Pending deposit"],
            ["Total value"],
            ["HR"],
            ["B"],
            ["AA"],
            ["A"],
        ]
