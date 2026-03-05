from oa_sdk.config import OAConfig
from oa_sdk.errors import TicketUsedError
from oa_sdk.keys import KeyService
from oa_sdk.models import KeyLease, Ticket, TicketExport
from oa_sdk.signatures import RequestKeySignatureVerification
from oa_sdk.tickets.store import TicketStore
from oa_sdk.transport import TransportResult


class FakeTransport:
    def __init__(self, result: TransportResult):
        self._result = result
        self.calls = []

    def request_json(self, *args, **kwargs):  # noqa: ANN002, ANN003
        self.calls.append((args, kwargs))
        return self._result


def test_request_key_success() -> None:
    service = KeyService(
        config=OAConfig(org_api_base="https://org.test"),
        transport=FakeTransport(
            TransportResult(
                status_code=200,
                data={
                    "key": "k",
                    "tickets_consumed": 1,
                    "station_id": "s",
                    "expires_at": "2026-01-01T00:00:00Z",
                },
                text="",
                headers={},
            )
        ),
    )

    lease = service.request_key_from_tokens(tokens=["t1"])
    assert lease.key == "k"
    assert lease.station_id == "s"


def test_fetch_online_stations_success() -> None:
    service = KeyService(
        config=OAConfig(org_api_base="https://org.test"),
        transport=FakeTransport(
            TransportResult(
                status_code=200,
                data={
                    "station-a": {
                        "url": "https://station-a.example",
                        "models": ["openai/gpt-5.2-chat"],
                        "providers": {"openai": {"gpt-5.2-chat": {"supported_tools": ["web_search"]}}},
                        "last_seen_seconds_ago": 5,
                        "version": 2,
                    }
                },
                text="",
                headers={},
            )
        ),
    )

    stations = service.fetch_online_stations(version=2)
    assert len(stations) == 1
    assert stations[0].station_id == "station-a"
    assert stations[0].url == "https://station-a.example"
    assert stations[0].version == 2


def test_request_key_spent_ticket_error() -> None:
    service = KeyService(
        config=OAConfig(org_api_base="https://org.test"),
        transport=FakeTransport(
            TransportResult(
                status_code=401,
                data={"detail": "double-spending detected"},
                text="",
                headers={},
            )
        ),
    )

    try:
        service.request_key_from_tokens(tokens=["t1"])
    except TicketUsedError:
        return
    assert False, "Expected TicketUsedError"


def test_request_key_from_store_archives_on_success() -> None:
    store = TicketStore(
        TicketExport(
            active=[Ticket(finalized_ticket="t1"), Ticket(finalized_ticket="t2")],
            archived=[],
        )
    )

    service = KeyService(
        config=OAConfig(org_api_base="https://org.test"),
        transport=FakeTransport(
            TransportResult(
                status_code=200,
                data={"key": "k", "station_id": "s", "tickets_consumed": 1},
                text="",
                headers={},
            )
        ),
    )

    lease = service.request_key_from_store(store=store, count=1)
    assert lease.key == "k"
    assert len(store.active) == 1
    assert len(store.archived) == 1


def test_fetch_org_public_key() -> None:
    transport = FakeTransport(
        TransportResult(
            status_code=200,
            data={"public_key": "ab" * 32},
            text="",
            headers={},
        )
    )
    service = KeyService(config=OAConfig(org_api_base="https://org.test"), transport=transport)

    public_key = service.fetch_org_public_key()

    assert public_key == "ab" * 32
    assert transport.calls
    assert transport.calls[0][1]["allow_retry"] is True


def test_verify_key_lease_signatures_delegates(monkeypatch) -> None:  # noqa: ANN001
    captured = {}
    expected = RequestKeySignatureVerification(station_signature_valid=True, org_signature_valid=True)

    def fake_verify_request_key_signatures(**kwargs):  # noqa: ANN003
        captured.update(kwargs)
        return expected

    monkeypatch.setattr("oa_sdk.keys.verify_request_key_signatures", fake_verify_request_key_signatures)

    service = KeyService(
        config=OAConfig(org_api_base="https://org.test"),
        transport=FakeTransport(
            TransportResult(status_code=200, data={}, text="", headers={}),
        ),
    )
    lease = KeyLease(
        key="k",
        tickets_consumed=1,
        station_id="s",
        expires_at_unix=123,
        station_signature="ab" * 64,
        org_signature="cd" * 64,
    )

    result = service.verify_key_lease_signatures(
        lease=lease,
        station_public_key_hex="11" * 32,
        org_public_key_hex="22" * 32,
    )

    assert result == expected
    assert captured["lease"] == lease
    assert captured["station_public_key_hex"] == "11" * 32
    assert captured["org_public_key_hex"] == "22" * 32
