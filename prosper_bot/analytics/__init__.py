import json
import logging
from datetime import date
from typing import List

from prosper_api.client import Client
from prosper_api.models import (
    ListNotesRequest,
    Note,
)
from prosper_api.models.enums import LoanStatus
from prosper_shared.omni_config import ConfigKey, config_schema
from pyxirr import xirr
from schema import Optional as SchemaOptional

# from prosper_bot.util import bucketize, print_histogram

logger = logging.getLogger(__file__)


@config_schema
def _schema():
    return {
        "prosper-bot": {
            "analytics": {
                SchemaOptional(
                    ConfigKey(
                        "irr-start-date",
                        "Start date for IRR calculation.",
                    )
                ): str,
            }
        }
    }


def analyze(client: Client):
    """Analyzes the account."""
    start_date = client._config.get("prosper-bot.analytics.irr-start-date")
    if start_date is None:
        # Launch date of Prosper
        start_date = date(2006, 1, 5).isoformat()

    all_notes: List[Note] = []
    all_recent_notes: List[Note] = []
    list_notes_request = ListNotesRequest(limit=100, offset=0)
    list_notes_response = None
    while not list_notes_response or len(list_notes_response.result) == 100:
        list_notes_response = client.list_notes(list_notes_request)
        all_notes.extend(list_notes_response.result)
        all_recent_notes.extend(
            [n for n in list_notes_response.result if n.origination_date > start_date]
        )
        list_notes_request = list_notes_request.model_copy(
            update={"offset": list_notes_request.offset + list_notes_request.limit}
        )

    logger.debug(f"Total notes: {len(all_notes)}")
    print(f"Total recent notes: {len(all_recent_notes)}")

    queried_notes = sorted(all_recent_notes, key=lambda n: n.origination_date)

    all_dates = [
        *[n.origination_date for n in queried_notes],
        # *[p.transaction_effective_date for p in completed_payments],
        date.today().isoformat(),
    ]
    all_cashflows = [
        *[-n.note_ownership_amount for n in queried_notes],
        sum(
            (
                (
                    n.principal_balance_pro_rata_share
                    if n.note_status
                    in [
                        LoanStatus.CURRENT,
                        LoanStatus.FINAL_PAYMENT_IN_PROGRESS,
                        LoanStatus.ORIGINATION_DELAYED,
                    ]
                    else 0
                )
                + n.principal_paid_pro_rata_share
                + n.interest_paid_pro_rata_share
                + n.debt_sale_proceeds_received_pro_rata_share
                + n.late_fees_paid_pro_rata_share
            )
            for n in queried_notes
        ),
    ]
    notes_by_rating = {}
    for note in all_notes:
        rating_notes = notes_by_rating.get(note.prosper_rating, None)
        if not rating_notes:
            notes_by_rating[note.prosper_rating] = rating_notes = []
        rating_notes.append(note)

    # print(f"Note: {note}")

    logger.debug(json.dumps(all_dates, indent=2))
    logger.debug(json.dumps([str(c) for c in all_cashflows], indent=2))
    overall_irr = xirr(all_dates, all_cashflows)

    logger.info(f"Overall IRR: {overall_irr:.2%}")

    # IRR by rating
    for rating, notes in notes_by_rating.items():
        dates = [n.origination_date for n in notes] + [date.today().isoformat()]
        cashflows = [-n.note_ownership_amount for n in notes] + [
            sum(
                (
                    n.principal_balance_pro_rata_share
                    if n.note_status
                    in [
                        LoanStatus.CURRENT,
                        LoanStatus.FINAL_PAYMENT_IN_PROGRESS,
                        LoanStatus.CHARGED_OFF,
                    ]
                    else 0
                )
                + n.principal_paid_pro_rata_share
                + n.interest_paid_pro_rata_share
                + n.debt_sale_proceeds_received_pro_rata_share
                + n.late_fees_paid_pro_rata_share
                for n in notes
            )
        ]
        irr = xirr(dates, cashflows)
        logger.info(f"IRR for {rating}: {irr:.2%}")

    # Oldest active note origination date
    oldest_active_note = min(
        n.origination_date for n in all_notes if n.note_status == LoanStatus.CURRENT
    )
    logger.info(f"Oldest active note date: {oldest_active_note}")

    # Newst active note origination date
    newest_active_note = max(
        n.origination_date for n in all_notes if n.note_status == LoanStatus.CURRENT
    )
    logger.info(f"Newest active note date: {newest_active_note}")
