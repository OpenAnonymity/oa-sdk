from __future__ import annotations

import os
from pathlib import Path

import pytest

from oa_sdk.client import OAClient
from oa_sdk.inference.models import ResponseRequest
from oa_sdk.tickets.store import TicketStore


pytestmark = pytest.mark.e2e_live


@pytest.mark.e2e_live
def test_live_request_key_and_inference_roundtrip() -> None:
    """
    Real network E2E test.

    Guardrails:
    - Skips unless OA_E2E_LIVE=1.
    - Consumes real tickets and persists updated ticket file.

    Required env:
    - OA_E2E_LIVE=1
    - OA_E2E_TICKETS_FILE=/path/to/tickets.json

    Optional env:
    - OA_E2E_MODEL (default: openai/gpt-5.2-chat)
    - OA_E2E_PROMPT (default: ping)
    - OA_E2E_TICKET_COUNT (default: 1)
    - OA_E2E_STATION_ID (optional)
    - OA_E2E_KEY_NAME (default: OA-SDK-E2E)
    """
    if os.getenv("OA_E2E_LIVE") != "1":
        pytest.skip("Set OA_E2E_LIVE=1 to run live E2E test")

    ticket_path = os.getenv("OA_E2E_TICKETS_FILE")
    if not ticket_path:
        pytest.fail("OA_E2E_TICKETS_FILE is required when OA_E2E_LIVE=1")

    tickets_file = Path(ticket_path)
    if not tickets_file.exists():
        pytest.fail(f"Tickets file does not exist: {tickets_file}")

    model = os.getenv("OA_E2E_MODEL", "openai/gpt-5.2-chat")
    prompt = os.getenv("OA_E2E_PROMPT", "ping")
    station_id = os.getenv("OA_E2E_STATION_ID")
    key_name = os.getenv("OA_E2E_KEY_NAME", "OA-SDK-E2E")

    ticket_count_env = os.getenv("OA_E2E_TICKET_COUNT", "1")
    try:
        ticket_count = int(ticket_count_env)
    except ValueError as exc:
        pytest.fail(f"OA_E2E_TICKET_COUNT must be an int, got: {ticket_count_env}")

    store = TicketStore.from_file(tickets_file)
    before_active = store.count_active()
    before_archived = len(store.archived)

    if before_active < ticket_count:
        pytest.fail(
            f"Not enough active tickets for E2E run. Need {ticket_count}, have {before_active}."
        )

    result = None
    try:
        with OAClient() as client:
            result = client.request_key_and_infer_openrouter(
                store=store,
                request=ResponseRequest(model=model, input=prompt),
                ticket_count=ticket_count,
                key_name=key_name,
                station_id=station_id,
            )
    finally:
        # Persist ticket state no matter what, so local file reflects any real ticket spend.
        store.save(tickets_file)

    assert result is not None
    assert result.key_lease.key
    assert result.key_lease.station_id
    assert result.key_lease.tickets_consumed >= ticket_count
    assert result.response.output_text is not None

    store_after = TicketStore.from_file(tickets_file)
    assert store_after.count_active() == before_active - ticket_count
    assert len(store_after.archived) == before_archived + ticket_count
