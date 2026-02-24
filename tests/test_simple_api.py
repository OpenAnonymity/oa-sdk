from __future__ import annotations

from pathlib import Path

import pytest

import oa
from oa_sdk.errors import OAProtocolError
from oa_sdk.models import KeyLease, OAResponse, StationInfo, Ticket, TicketExport, TicketRedeemResult
from oa_sdk.tickets.store import TicketStore


class FakeKeyService:
    def fetch_model_tickets(self) -> dict[str, int]:
        return {"openai/gpt-5.2-chat": 1}

    def fetch_online_stations(self, *, version: int = 2) -> list[StationInfo]:
        assert version in (1, 2)
        return [
            StationInfo(
                station_id="station-a",
                url="https://station-a.example",
                models=["openai/gpt-5.2-chat"],
                providers={"openai": {"gpt-5.2-chat": {"supported_tools": ["web_search"]}}},
                last_seen_seconds_ago=3,
                version=version,
            )
        ]

    def request_key_from_store(  # noqa: ANN001
        self,
        *,
        store,
        count,
        name,
        station_id=None,
    ) -> KeyLease:
        selected = store.select(count)
        store.archive_selected(selected, status="consumed")
        return KeyLease(
            key="ek-test",
            tickets_consumed=count,
            station_id=station_id or "station-default",
            station_signature="station-sig" if station_id else None,
            org_signature="org-sig" if station_id else None,
        )


class FakeInferenceService:
    def openrouter_ephemeral_backend(self, *, base_url=None):  # noqa: ANN001, ANN201
        return ("openrouter", base_url)

    def gemini_provider_direct_backend(self, *, base_url=None):  # noqa: ANN001, ANN201
        return ("gemini-provider-direct", base_url)

    def openai_provider_direct_backend(self, *, base_url=None):  # noqa: ANN001, ANN201
        return ("openai-provider-direct", base_url)

    def provider_direct_backend(self, *, base_url):  # noqa: ANN001, ANN201
        return ("provider-direct", base_url)

    def tee_gateway_backend(self, *, base_url, extra_headers=None):  # noqa: ANN001, ANN201
        return ("tee-gateway", base_url, extra_headers)

    def create_response(self, request, *, backend, credential):  # noqa: ANN001
        return OAResponse(
            response_id="resp_1",
            output_text=f"{backend[0]}:{request.model}:{credential.token}",
            raw={"backend": backend[0]},
        )


class FakeTicketService:
    _counter = 0

    def redeem_code(self, *, credential, requested_count=None, store=None):  # noqa: ANN001
        count = requested_count or 1
        tickets = []
        for _ in range(count):
            self.__class__._counter += 1
            tickets.append(Ticket(finalized_ticket=f"{credential}-{self._counter}"))
        if store is not None:
            store.extend_active(tickets)
        return TicketRedeemResult(
            tickets_issued=len(tickets),
            expires_at=None,
            public_key="pk-test",
            tickets=tickets,
        )


class FakeClient:
    def __init__(self, config=None):  # noqa: ANN001
        self.keys = FakeKeyService()
        self.inference = FakeInferenceService()
        self.tickets = FakeTicketService()

    def __enter__(self):  # noqa: ANN204
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001, ANN204
        return None


@pytest.fixture(autouse=True)
def _patch_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("oa_sdk.simple.OAClient", FakeClient)


def _seed_ticket_file(path: Path, count: int) -> None:
    export = TicketExport(
        active=[Ticket(finalized_ticket=f"t{i}") for i in range(count)],
        archived=[],
    )
    TicketStore(export).save(path)


def test_request_unlinkable_key_consumes_and_persists(tmp_path: Path) -> None:
    ticket_file = tmp_path / "tickets.json"
    _seed_ticket_file(ticket_file, count=2)

    payload = oa.request_unlinkable_key(ticket_file=ticket_file, ticket_count=1)
    assert payload["key"] == "ek-test"
    assert payload["active_tickets"] == 1
    assert payload["archived_tickets"] == 1

    saved = TicketStore.from_file(ticket_file)
    assert saved.count_active() == 1
    assert len(saved.archived) == 1


def test_list_stations_exposes_org_station_data() -> None:
    payload = oa.list_stations(version=2)
    assert payload["version"] == 2
    assert payload["total"] == 1
    assert payload["stations"][0]["station_id"] == "station-a"
    assert payload["stations"][0]["url"] == "https://station-a.example"


def test_request_confidential_key_attestation_check(tmp_path: Path) -> None:
    ticket_file = tmp_path / "tickets.json"
    _seed_ticket_file(ticket_file, count=1)

    with pytest.raises(OAProtocolError):
        oa.request_confidential_key(
            ticket_file=ticket_file,
            ticket_count=1,
            require_attestation=True,
        )


def test_request_confidential_key_does_not_accept_station_pin(tmp_path: Path) -> None:
    ticket_file = tmp_path / "tickets.json"
    _seed_ticket_file(ticket_file, count=1)

    with pytest.raises(TypeError):
        oa.request_confidential_key(  # type: ignore[call-arg]
            ticket_file=ticket_file,
            ticket_count=1,
            station_id="station-a",
        )


def test_chat_completion_simple_call() -> None:
    payload = oa.chat_completion(
        key="ek-test",
        model="openai/gpt-5.2-chat",
        prompt="hello",
        destination="openrouter",
    )
    assert payload["response_id"] == "resp_1"
    assert payload["output_text"] == "openrouter:openai/gpt-5.2-chat:ek-test"


def test_chat_completion_provider_direct_requires_base_url() -> None:
    with pytest.raises(ValueError):
        oa.chat_completion(
            key="ek-test",
            model="gpt-5",
            prompt="hello",
            destination="provider-direct",
        )


def test_add_show_archive_tickets(tmp_path: Path) -> None:
    ticket_file = tmp_path / "tickets.json"

    added = oa.add_tickets("cred-abc", ticket_file=ticket_file, requested_count=2)
    assert added["tickets_issued"] == 2
    assert added["active_tickets"] == 2

    view = oa.show_tickets(ticket_file=ticket_file, include_tokens=False, limit=1)
    assert view["active_tickets"] == 2
    assert len(view["active"]) == 1
    assert "finalized_ticket" not in view["active"][0]

    moved = oa.archive_tickets(ticket_file=ticket_file, count=1)
    assert moved["moved"] == 1
    assert moved["active_tickets"] == 1
    assert moved["archived_tickets"] == 1
