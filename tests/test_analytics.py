import pytest
from prosper_api.models import ListNotesResponse, Note
from prosper_api.models.enums import LoanStatus

from prosper_bot.analytics import analyze


class TestAnalytics:

    @pytest.fixture
    def client_mock(self, mocker):
        return mocker.patch("prosper_bot.bot.bot.Client")

    def test_analytics(self, client_mock, caplog):
        client_mock._config.get.return_value = None
        client_mock.list_notes.return_value = ListNotesResponse(
            result=[
                Note(
                    origination_date="2021-01-02",
                    principal_balance_pro_rata_share=69.7381,
                    service_fees_paid_pro_rata_share=-0.589991,
                    principal_paid_pro_rata_share=15.8919,
                    interest_paid_pro_rata_share=14.749939,
                    prosper_fees_paid_pro_rata_share=0.0,
                    late_fees_paid_pro_rata_share=0.0,
                    collection_fees_paid_pro_rata_share=0.0,
                    debt_sale_proceeds_received_pro_rata_share=0.0,
                    platform_proceeds_net_received=0.0,
                    next_payment_due_amount_pro_rata_share=3.404649,
                    note_ownership_amount=85.63,
                    note_sale_gross_amount_received=0.0,
                    note_sale_fees_paid=0.0,
                    loan_note_id="35659-26",
                    listing_number=111111,
                    note_status=LoanStatus.CURRENT,
                    note_status_description="CURRENT",
                    note_default_reason=3,
                    note_default_reason_description="Bankruptcy",
                    is_sold=False,
                    is_sold_folio=False,
                    loan_number=11111,
                    amount_borrowed=5000.0,
                    borrower_rate=0.25,
                    lender_yield=0.24,
                    prosper_rating="N/A",
                    term=36,
                    age_in_months=182,
                    accrued_interest=97.871494,
                    payment_received=30.051848,
                    loan_settlement_status="Unspecified",
                    loan_extension_status="Unspecified",
                    loan_extension_term=0,
                    is_in_bankruptcy=False,
                    co_borrower_application=False,
                    days_past_due=123,
                    next_payment_due_date="2011-08-19",
                    ownership_start_date="2008-08-19",
                ),
            ],
            result_count=1,
            total_count=1,
        )

        with caplog.at_level("INFO"):
            analyze(client_mock)

        assert len(caplog.records) == 4
        assert caplog.records[0].message == "Overall IRR: 3.93%"
        assert caplog.records[1].message == "IRR for N/A: 3.93%"
        assert caplog.records[2].message == "Oldest active note date: 2021-01-02"
        assert caplog.records[3].message == "Newest active note date: 2021-01-02"
