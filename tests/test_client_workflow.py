from __future__ import annotations

from oa_sdk.client import OAClient
from oa_sdk.config import OAConfig
from oa_sdk.inference.models import ResponseRequest
from oa_sdk.models import KeyLease, OAResponse, Ticket, TicketExport
from oa_sdk.tickets.store import TicketStore


class FakeKeyService:
    def __init__(self) -> None:
        self.last_count = None

    def fetch_model_tickets(self) -> dict[str, int]:
        return {"openai/gpt-5.2-chat": 2}

    def request_key_from_store(self, *, store, count, name, station_id):  # noqa: ANN001
        self.last_count = count
        assert store.count_active() >= count
        selected = store.select(count)
        store.archive_selected(selected)
        return KeyLease(
            key="ek-test",
            tickets_consumed=count,
            station_id="station-1",
            expires_at="2026-01-01T00:00:00Z",
        )


class FakeInferenceService:
    def openrouter_ephemeral_backend(self):  # noqa: ANN201
        return "openrouter-backend"

    def create_response(self, request, *, backend, credential):  # noqa: ANN001
        assert backend == "openrouter-backend"
        assert credential.token == "ek-test"
        return OAResponse(response_id="resp_1", output_text=f"echo:{request.model}", raw={})


def test_client_request_key_and_infer_openrouter_uses_model_cost() -> None:
    store = TicketStore(
        TicketExport(
            active=[Ticket(finalized_ticket="t1"), Ticket(finalized_ticket="t2"), Ticket(finalized_ticket="t3")],
            archived=[],
        )
    )

    with OAClient(config=OAConfig(org_api_base="https://org.test")) as client:
        client.keys = FakeKeyService()  # type: ignore[assignment]
        client.inference = FakeInferenceService()  # type: ignore[assignment]

        result = client.request_key_and_infer_openrouter(
            store=store,
            request=ResponseRequest(model="openai/gpt-5.2-chat", input="hi"),
        )

    assert result.key_lease.tickets_consumed == 2
    assert result.response.output_text == "echo:openai/gpt-5.2-chat"
    assert len(store.active) == 1
    assert len(store.archived) == 2
