from decimal import Decimal

import pytest
from prosper_api.client import Client
from prosper_api.models import (
    Account,
    AmountsByRating,
    Listing,
    SearchListingsRequest,
    SearchListingsResponse,
)
from prosper_api.models.enums import EmploymentStatus, ProsperRating

from prosper_bot.allocation_strategy import (
    _BASE_REQUEST,
    AllocationStrategies,
    AllocationStrategy,
    FixedTargetAllocationStrategy,
    HighestMatchingRateAllocationStrategy,
)


class TestAllocationStrategy:
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
        last_deposit_date="2023-12-04T08:00Z",
        last_withdraw_amount=Decimal("-14.31"),
        last_withdraw_date="2023-12-04T08:00Z",
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

    def minimal_listing(self, listing_num: int) -> Listing:
        return Listing(
            listing_title=f"listing {listing_num}",
            prosper_rating="N/A",
            listing_number=listing_num,
            listing_start_date="1234-12-34",
            listing_creation_date="4321-43-21",
            listing_status=2,
            listing_status_reason="BLAH",
            invested=True,
            biddable=True,
            has_mortgage=True,
            credit_bureau_values_transunion_indexed={
                "g102s_months_since_most_recent_inquiry": 3,
                "credit_report_date": "some-date",
                "at02s_open_accounts": 3,
                "g041s_accounts_30_or_more_days_past_due_ever": 1,
                "g093s_number_of_public_records": 0,
                "g094s_number_of_public_record_bankruptcies": 0,
                "g095s_months_since_most_recent_public_record": -1,
                "g218b_number_of_delinquent_accounts": 5,
                "g980s_inquiries_in_the_last_6_months": 4,
                "re20s_age_of_oldest_revolving_account_in_months": 50,
                "s207s_months_since_most_recent_public_record_bankruptcy": -1,
                "re33s_balance_owed_on_all_revolving_accounts": 40000,
                "at57s_amount_delinquent": 0,
                "g099s_public_records_last_24_months": 0,
                "at20s_oldest_trade_open_date": 1234.5678,
                "at03s_current_credit_lines": 15,
                "re101s_revolving_balance": 40000,
                "bc34s_bankcard_utilization": 0.5,
                "at01s_credit_lines": 20,
                "fico_score": "<600",
            },
            employment_status_description=EmploymentStatus.EMPLOYED,
            investment_type_description="BLAH",
            last_updated_date="2345-67-89",
            decision_bureau="blah",
            member_key="1",
            borrower_state="CA",
            co_borrower_application=False,
            income_verifiable=True,
            lender_yield=listing_num + 0.8,
        )

    @pytest.fixture
    def mock_client(self, mocker) -> Client:
        client = mocker.MagicMock()
        client.search_listings.side_effect = lambda x: SearchListingsResponse(
            result=[self.minimal_listing(listing_num) for listing_num in range(10)],
            result_count=10,
            total_count=10,
        )
        client.get_account_info.return_value = self.TEST_ACCOUNT
        return client

    def test_allocation_strategy_with_matching_listings(self, mock_client):
        api_params = [SearchListingsRequest()]

        allocation_strategy = AllocationStrategy(
            mock_client, search_request_iterator=iter(api_params)
        )
        assert [listing.listing_number for listing in allocation_strategy] == [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
        ]

    def test_allocation_strategy_no_matching_listings(self, mock_client):
        api_params = []

        mock_client.search_listings.return_value = SearchListingsResponse(
            result=[], result_count=0, total_count=0
        )

        allocation_strategy = AllocationStrategy(
            mock_client, search_request_iterator=iter(api_params)
        )
        with pytest.raises(StopIteration):
            next(allocation_strategy)

    def test_allocation_strategy_iteration_timeout(self, mock_client):
        api_params = [SearchListingsRequest()]

        allocation_strategy = AllocationStrategy(
            mock_client,
            search_request_iterator=iter(api_params),
            timeout_seconds=0.0000000001,
        )
        with pytest.raises(StopIteration):
            next(allocation_strategy)

    def test_allocation_strategy_with_local_sort(self, mock_client):
        api_params = [SearchListingsRequest()]

        allocation_strategy = AllocationStrategy(
            mock_client,
            search_request_iterator=iter(api_params),
            local_sort=lambda listing: -listing.listing_number,
        )
        assert [listing.listing_number for listing in allocation_strategy] == [
            9,
            8,
            7,
            6,
            5,
            4,
            3,
            2,
            1,
            0,
        ]

    def test_highest_allocation_strategy(self, mock_client):
        allocation_strategy = HighestMatchingRateAllocationStrategy(
            mock_client, AllocationStrategies.OVERALL_HIGHEST_RATE.value[1]
        )

        assert [r.sort_by for r in allocation_strategy._search_requests] == [
            "lender_yield"
        ]

    def test_fixed_target_allocation_strategy(self, mock_client):
        allocation_strategy = FixedTargetAllocationStrategy(
            mock_client, AllocationStrategies.AGGRESSIVE.value[1]
        )

        assert [r.prosper_rating for r in allocation_strategy._search_requests] == [
            [ProsperRating.D],
            [ProsperRating.E],
            [ProsperRating.C],
            [ProsperRating.HR],
            [ProsperRating.B],
            [ProsperRating.AA],
            [ProsperRating.A],
        ]

    @pytest.mark.parametrize(
        ["strategy_enum", "expected_class", "expected_search_request"],
        [
            (
                AllocationStrategies.AGGRESSIVE,
                FixedTargetAllocationStrategy,
                [
                    {"prosper_rating": ["D"]},
                    {"prosper_rating": ["E"]},
                    {"prosper_rating": ["C"]},
                    {"prosper_rating": ["HR"]},
                    {"prosper_rating": ["B"]},
                    {"prosper_rating": ["AA"]},
                    {"prosper_rating": ["A"]},
                ],
            ),
            (
                AllocationStrategies.CONSERVATIVE,
                FixedTargetAllocationStrategy,
                [
                    {"prosper_rating": ["A"]},
                    {"prosper_rating": ["AA"]},
                    {"prosper_rating": ["B"]},
                    {"prosper_rating": ["HR"]},
                    {"prosper_rating": ["C"]},
                    {"prosper_rating": ["D"]},
                    {"prosper_rating": ["E"]},
                ],
            ),
            (
                AllocationStrategies.OVERALL_HIGHEST_RATE,
                HighestMatchingRateAllocationStrategy,
                [
                    {},
                ],
            ),
        ],
    )
    def test_allocation_strategies_to_strategy(
        self, mock_client, strategy_enum, expected_class, expected_search_request
    ):
        strategy = strategy_enum.to_strategy(mock_client)

        assert isinstance(strategy, expected_class)
        assert strategy._search_requests == [
            SearchListingsRequest(**{**_BASE_REQUEST.model_dump(), **r})
            for r in expected_search_request
        ]
