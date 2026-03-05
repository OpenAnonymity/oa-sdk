from __future__ import annotations

from oa_sdk.models import Ticket, TicketExport
from oa_sdk.tickets.store import TicketStore


def test_extend_active_skips_duplicates_in_active_and_archived() -> None:
    store = TicketStore(
        TicketExport(
            active=[Ticket(finalized_ticket="active-1")],
            archived=[Ticket(finalized_ticket="archived-1", status="archived")],
        )
    )

    store.extend_active(
        [
            Ticket(finalized_ticket="active-1"),
            Ticket(finalized_ticket="archived-1"),
            Ticket(finalized_ticket="new-1"),
        ]
    )

    assert [ticket.finalized_ticket for ticket in store.active] == ["active-1", "new-1"]
    assert [ticket.finalized_ticket for ticket in store.archived] == ["archived-1"]
