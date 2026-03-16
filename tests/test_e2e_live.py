from __future__ import annotations

import os
from pathlib import Path

import pytest

from oa_sdk.client import OAClient
from oa_sdk.inference.models import ResponseRequest
from oa_sdk.tickets.store import TicketStore


pytestmark = pytest.mark.e2e_live


def _report_live_e2e_ticket_usage(
    pytestconfig: pytest.Config,
    *,
    phase: str,
    requested_tickets: int,
    model: str | None,
    active_before: int,
    archived_before: int,
    consumed_tickets: int | None = None,
    active_after: int | None = None,
    archived_after: int | None = None,
) -> None:
    reporter = pytestconfig.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:
        return

    parts = [
        f"phase={phase}",
        f"requested_tickets={requested_tickets}",
        f"active_before={active_before}",
        f"archived_before={archived_before}",
    ]
    if model:
        parts.append(f"model={model}")
    if consumed_tickets is not None:
        parts.append(f"consumed_tickets={consumed_tickets}")
    if active_after is not None:
        parts.append(f"active_after={active_after}")
    if archived_after is not None:
        parts.append(f"archived_after={archived_after}")

    reporter.write_line("[oa-sdk live e2e] " + " ".join(parts))


@pytest.mark.e2e_live
def test_live_request_key_and_inference_roundtrip(pytestconfig: pytest.Config) -> None:
    """
    Real network E2E test.

    Guardrails:
    - Skips unless OA_E2E_LIVE=1.
    - Consumes real tickets and persists updated ticket file.

    Required env:
    - OA_E2E_LIVE=1
    - OA_E2E_TICKETS_FILE=/path/to/tickets.json

    Optional env:
    - OA_E2E_MODEL (default: latest OA-supported free model from OpenRouter catalog)
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

    model = os.getenv("OA_E2E_MODEL")
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
    resolved_model: str | None = model
    store_after = None
    try:
        with OAClient() as client:
            if not resolved_model:
                supported_models = client.keys.fetch_model_tickets().keys()
                resolved_model = client.inference.latest_openrouter_free_model(
                    allowed_model_ids=supported_models
                ).id
            assert resolved_model is not None
            _report_live_e2e_ticket_usage(
                pytestconfig,
                phase="planned-spend",
                requested_tickets=ticket_count,
                model=resolved_model,
                active_before=before_active,
                archived_before=before_archived,
            )

            result = client.request_key_and_infer_openrouter(
                store=store,
                request=ResponseRequest(model=resolved_model, input=prompt),
                ticket_count=ticket_count,
                key_name=key_name,
                station_id=station_id,
            )
    finally:
        # Persist ticket state no matter what, so local file reflects any real ticket spend.
        store.save(tickets_file)
        store_after = TicketStore.from_file(tickets_file)
        consumed_tickets = (
            result.key_lease.tickets_consumed
            if result is not None
            else before_active - store_after.count_active()
        )
        _report_live_e2e_ticket_usage(
            pytestconfig,
            phase="result",
            requested_tickets=ticket_count,
            consumed_tickets=consumed_tickets,
            model=resolved_model,
            active_before=before_active,
            active_after=store_after.count_active(),
            archived_before=before_archived,
            archived_after=len(store_after.archived),
        )

    assert result is not None
    assert result.key_lease.key
    assert result.key_lease.station_id
    assert result.key_lease.tickets_consumed >= ticket_count
    assert result.response.output_text is not None

    assert store_after is not None
    assert store_after.count_active() == before_active - ticket_count
    assert len(store_after.archived) == before_archived + ticket_count
