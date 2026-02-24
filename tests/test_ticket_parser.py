from oa_sdk.tickets.parser import parse_ticket_export


def test_parse_nested_export_active_and_archived() -> None:
    payload = {
        "data": {
            "tickets": {
                "active": [
                    {"finalized_ticket": "t1", "created_at": "now"},
                    {"finalized_ticket": "t2", "consumed_at": "now", "status": "consumed"},
                ]
            }
        }
    }

    parsed = parse_ticket_export(payload)
    assert len(parsed.active) == 1
    assert parsed.active[0].finalized_ticket == "t1"
    assert len(parsed.archived) == 1
    assert parsed.archived[0].finalized_ticket == "t2"


def test_parse_raw_array_export() -> None:
    payload = [
        {"finalized_ticket": "x"},
        {"finalized_ticket": "y", "status": "archived"},
    ]

    parsed = parse_ticket_export(payload)
    assert [ticket.finalized_ticket for ticket in parsed.active] == ["x"]
    assert [ticket.finalized_ticket for ticket in parsed.archived] == ["y"]


def test_parse_active_archived_variants() -> None:
    payload = {
        "activeTickets": [{"finalized_ticket": "a1"}],
        "archivedTickets": [{"finalized_ticket": "a2"}],
    }

    parsed = parse_ticket_export(payload)
    assert len(parsed.active) == 1
    assert len(parsed.archived) == 1
