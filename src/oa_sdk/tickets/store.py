from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Literal

from ..errors import InsufficientTicketsError
from ..models import Ticket, TicketExport
from .parser import dump_ticket_export_file, load_ticket_export_file

Order = Literal["head", "tail"]


@dataclass
class SelectedTickets:
    tickets: List[Ticket]

    def finalized_tokens(self) -> List[str]:
        return [ticket.finalized_ticket for ticket in self.tickets]


class TicketStore:
    def __init__(self, tickets: TicketExport | None = None) -> None:
        data = tickets or TicketExport()
        self.active: List[Ticket] = list(data.active)
        self.archived: List[Ticket] = list(data.archived)

    @classmethod
    def from_file(cls, path: str | Path) -> TicketStore:
        return cls(load_ticket_export_file(path))

    def save(self, path: str | Path) -> None:
        dump_ticket_export_file(path, self.to_export())

    def to_export(self) -> TicketExport:
        return TicketExport(active=list(self.active), archived=list(self.archived))

    def count_active(self) -> int:
        return len(self.active)

    def select(self, count: int, *, order: Order = "head") -> SelectedTickets:
        if count <= 0:
            raise ValueError("count must be positive")
        if len(self.active) < count:
            raise InsufficientTicketsError(f"Need {count} tickets, have {len(self.active)}")

        if order == "head":
            selected = self.active[:count]
        elif order == "tail":
            selected = self.active[-count:]
        else:
            raise ValueError(f"Unsupported selection order: {order}")

        return SelectedTickets(tickets=list(selected))

    def archive_selected(self, selected: SelectedTickets, *, status: str = "consumed") -> None:
        selected_ids = {ticket.finalized_ticket for ticket in selected.tickets}
        if not selected_ids:
            return

        now = datetime.now(timezone.utc).isoformat()
        remaining: List[Ticket] = []
        moved: List[Ticket] = []

        for ticket in self.active:
            if ticket.finalized_ticket in selected_ids:
                ticket.archive(consumed_at=now, status=status)
                moved.append(ticket)
            else:
                remaining.append(ticket)

        self.active = remaining
        self.archived.extend(moved)

    def extend_active(self, tickets: Iterable[Ticket]) -> None:
        existing = {ticket.finalized_ticket for ticket in self.active}
        for ticket in tickets:
            if ticket.finalized_ticket in existing:
                continue
            self.active.append(ticket)
            existing.add(ticket.finalized_ticket)
