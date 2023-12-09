import pytest
from prosper_api.client import Client
from prosper_api.models import Listing, SearchListingsRequest, SearchListingsResponse
from prosper_api.models.enums import EmploymentStatus

from prosper_bot.allocation_strategy import AllocationStrategy


class TestAllocationStrategy:
    def minimal_listing(self, listing_num: int) -> Listing:
        return Listing(
            listing_title=f"listing {listing_num}",
            prosper_rating="N/A",
            listing_number=listing_num,
            listing_start_date="1234-12-34",
            listing_creation_date="4321-43-21",
            listing_status="BLAH",
            listing_status_reason="BLAH",
            invested=True,
            biddable=True,
            has_mortgage=True,
            credit_bureau_values_transunion_indexed={},
            employment_status_description=EmploymentStatus.EMPLOYED,
            investment_type_description="BLAH",
            last_updated_date="2345-67-89",
            decision_bureau="blah",
            member_key=1,
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
        return client

    def test_allocation_strategy_one_matching_listing(self, mock_client):
        api_params = [SearchListingsRequest()]

        allocation_strategy = AllocationStrategy(
            mock_client, api_param_iterator=iter(api_params)
        )
        assert len(list(allocation_strategy)) == 10

    def test_allocation_strategy_ten_matching_listings(self, mock_client):
        api_params = []

        mock_client.search_listings.return_value = SearchListingsResponse(
            result=[], result_count=0, total_count=0
        )

        allocation_strategy = AllocationStrategy(
            mock_client, api_param_iterator=iter(api_params)
        )
        with pytest.raises(StopIteration):
            next(allocation_strategy)
