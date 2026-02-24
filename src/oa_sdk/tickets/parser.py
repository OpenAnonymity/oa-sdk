from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from ..errors import TicketFormatError
from ..models import Ticket, TicketExport


def parse_ticket_export(payload: Any) -> TicketExport:
    if isinstance(payload, list):
        return _split_ticket_list(payload)

    if not isinstance(payload, dict):
        raise TicketFormatError("Invalid ticket payload: expected object or list")

    container = payload
    if "data" in container and isinstance(container["data"], dict):
        container = container["data"]

    if "tickets" in container and isinstance(container["tickets"], dict):
        container = container["tickets"]

    if "active" in container or "archived" in container:
        active_candidates = _parse_ticket_list(container.get("active", []))
        active: List[Ticket] = []
        inferred_archived: List[Ticket] = []
        for ticket in active_candidates:
            if ticket.is_active():
                active.append(ticket)
            else:
                inferred_archived.append(ticket)

        archived = _parse_ticket_list(container.get("archived", []), archive_default=True)
        archived.extend(inferred_archived)
        return TicketExport(active=active, archived=archived)

    if "activeTickets" in container or "archivedTickets" in container:
        active = _parse_ticket_list(container.get("activeTickets", []))
        archived = _parse_ticket_list(container.get("archivedTickets", []), archive_default=True)
        return TicketExport(active=active, archived=archived)

    if "tickets" in container and isinstance(container["tickets"], list):
        return _split_ticket_list(container["tickets"])

    if isinstance(container, list):
        return _split_ticket_list(container)

    raise TicketFormatError("No tickets found in payload")


def load_ticket_export_file(path: str | Path) -> TicketExport:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_ticket_export(data)


def dump_ticket_export_file(path: str | Path, tickets: TicketExport) -> None:
    payload = {
        "data": {
            "tickets": {
                "active": [_ticket_to_dict(ticket) for ticket in tickets.active],
                "archived": [_ticket_to_dict(ticket) for ticket in tickets.archived],
            }
        }
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _split_ticket_list(values: Iterable[Any]) -> TicketExport:
    parsed = _parse_ticket_list(values)
    active: List[Ticket] = []
    archived: List[Ticket] = []
    for ticket in parsed:
        if ticket.is_active():
            active.append(ticket)
        else:
            archived.append(ticket)
    return TicketExport(active=active, archived=archived)


def _parse_ticket_list(values: Any, *, archive_default: bool = False) -> List[Ticket]:
    if not isinstance(values, list):
        return []

    parsed: List[Ticket] = []
    for item in values:
        if not isinstance(item, dict):
            continue
        finalized = item.get("finalized_ticket")
        if not isinstance(finalized, str) or not finalized.strip():
            continue
        ticket = Ticket(
            finalized_ticket=finalized,
            blinded_request=_opt_str(item.get("blinded_request")),
            signed_response=_opt_str(item.get("signed_response")),
            created_at=_opt_str(item.get("created_at")),
            consumed_at=_opt_str(item.get("consumed_at") or item.get("used_at")),
            status=_opt_str(item.get("status")),
        )
        if archive_default and ticket.is_active():
            ticket.archive(status=ticket.status or "archived")
        parsed.append(ticket)
    return parsed


def _ticket_to_dict(ticket: Ticket) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "finalized_ticket": ticket.finalized_ticket,
    }
    if ticket.blinded_request:
        value["blinded_request"] = ticket.blinded_request
    if ticket.signed_response:
        value["signed_response"] = ticket.signed_response
    if ticket.created_at:
        value["created_at"] = ticket.created_at
    if ticket.consumed_at:
        value["consumed_at"] = ticket.consumed_at
    if ticket.status:
        value["status"] = ticket.status
    return value


def _opt_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None
