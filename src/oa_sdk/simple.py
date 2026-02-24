from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Mapping

from .client import OAClient
from .config import OAConfig
from .errors import OAProtocolError
from .inference.backends import InferenceBackend
from .inference.models import AccessCredential, ResponseRequest
from .models import KeyLease, StationInfo, Ticket
from .tickets.store import Order, TicketStore

Destination = Literal[
    "openrouter",
    "gemini-provider-direct",
    "openai-provider-direct",
    "provider-direct",
    "tee-gateway",
]

DEFAULT_TICKET_FILE = "oa-chat-tickets.json"
DEFAULT_KEY_NAME = "OA-SDK-Key"


def request_unlinkable_key(
    ticket_file: str | Path = DEFAULT_TICKET_FILE,
    *,
    ticket_count: int = 1,
    key_name: str = DEFAULT_KEY_NAME,
    save: bool = True,
    config: OAConfig | None = None,
) -> dict[str, Any]:
    path = _ticket_file_path(ticket_file)
    store = TicketStore.from_file(path)

    with OAClient(config=config) as client:
        lease = client.keys.request_key_from_store(
            store=store,
            count=ticket_count,
            name=key_name,
        )

    if save:
        store.save(path)

    payload = _key_lease_payload(lease)
    payload.update(
        {
            "ticket_file": str(path),
            "active_tickets": store.count_active(),
            "archived_tickets": len(store.archived),
        }
    )
    return payload


def request_confidential_key(
    ticket_file: str | Path = DEFAULT_TICKET_FILE,
    *,
    ticket_count: int = 1,
    key_name: str = DEFAULT_KEY_NAME,
    require_attestation: bool = False,
    save: bool = True,
    config: OAConfig | None = None,
) -> dict[str, Any]:
    payload = request_unlinkable_key(
        ticket_file=ticket_file,
        ticket_count=ticket_count,
        key_name=key_name,
        save=save,
        config=config,
    )

    if require_attestation and not (payload.get("station_signature") and payload.get("org_signature")):
        raise OAProtocolError(
            "Confidential key flow requested attestation, but station/org signatures were missing. "
            "The key request itself may still have succeeded and consumed tickets."
        )

    payload["mode"] = "confidential"
    return payload


def list_stations(
    *,
    version: Literal[1, 2] = 2,
    config: OAConfig | None = None,
) -> dict[str, Any]:
    with OAClient(config=config) as client:
        stations = client.keys.fetch_online_stations(version=version)

    return {
        "version": version,
        "total": len(stations),
        "stations": [_station_payload(station) for station in stations],
    }


def chat_completion(
    *,
    key: str,
    model: str,
    prompt: str,
    destination: Destination = "openrouter",
    base_url: str | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    extra: Mapping[str, Any] | None = None,
    extra_headers: Mapping[str, str] | None = None,
    config: OAConfig | None = None,
) -> dict[str, Any]:
    request = ResponseRequest(
        model=model,
        input=prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        extra=extra or {},
    )

    with OAClient(config=config) as client:
        backend = _resolve_backend(
            client=client,
            destination=destination,
            base_url=base_url,
            extra_headers=extra_headers,
        )
        response = client.inference.create_response(
            request,
            backend=backend,
            credential=AccessCredential(token=key),
        )

    return {
        "response_id": response.response_id,
        "output_text": response.output_text,
        "raw": response.raw,
    }


def add_tickets(
    credential: str,
    ticket_file: str | Path = DEFAULT_TICKET_FILE,
    *,
    requested_count: int | None = None,
    save: bool = True,
    config: OAConfig | None = None,
) -> dict[str, Any]:
    path = _ticket_file_path(ticket_file)
    store = TicketStore.from_file(path) if path.exists() else TicketStore()

    with OAClient(config=config) as client:
        result = client.tickets.redeem_code(
            credential=credential,
            requested_count=requested_count,
            store=store,
        )

    if save:
        store.save(path)

    return {
        "ticket_file": str(path),
        "tickets_issued": result.tickets_issued,
        "expires_at": result.expires_at,
        "public_key": result.public_key,
        "active_tickets": store.count_active(),
        "archived_tickets": len(store.archived),
    }


def show_tickets(
    ticket_file: str | Path = DEFAULT_TICKET_FILE,
    *,
    include_tokens: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    if limit < 0:
        raise ValueError("limit must be >= 0")

    path = _ticket_file_path(ticket_file)
    if path.exists():
        store = TicketStore.from_file(path)
    else:
        store = TicketStore()

    return {
        "ticket_file": str(path),
        "exists": path.exists(),
        "active_tickets": store.count_active(),
        "archived_tickets": len(store.archived),
        "active": [_ticket_preview(ticket, include_tokens=include_tokens) for ticket in store.active[:limit]],
        "archived": [
            _ticket_preview(ticket, include_tokens=include_tokens)
            for ticket in store.archived[:limit]
        ],
    }


def archive_tickets(
    ticket_file: str | Path = DEFAULT_TICKET_FILE,
    *,
    count: int = 1,
    order: Order = "head",
    status: str = "archived",
    save: bool = True,
) -> dict[str, Any]:
    path = _ticket_file_path(ticket_file)
    store = TicketStore.from_file(path)
    selected = store.select(count, order=order)
    store.archive_selected(selected, status=status)

    if save:
        store.save(path)

    return {
        "ticket_file": str(path),
        "moved": len(selected.tickets),
        "status": status,
        "active_tickets": store.count_active(),
        "archived_tickets": len(store.archived),
    }


def _resolve_backend(
    *,
    client: OAClient,
    destination: Destination,
    base_url: str | None,
    extra_headers: Mapping[str, str] | None,
) -> InferenceBackend:
    if destination == "openrouter":
        return client.inference.openrouter_ephemeral_backend(base_url=base_url)
    if destination == "gemini-provider-direct":
        return client.inference.gemini_provider_direct_backend(base_url=base_url)
    if destination == "openai-provider-direct":
        return client.inference.openai_provider_direct_backend(base_url=base_url)
    if destination == "provider-direct":
        if not base_url:
            raise ValueError("base_url is required when destination='provider-direct'")
        return client.inference.provider_direct_backend(base_url=base_url)
    if not base_url:
        raise ValueError("base_url is required when destination='tee-gateway'")
    return client.inference.tee_gateway_backend(base_url=base_url, extra_headers=extra_headers)


def _key_lease_payload(lease: KeyLease) -> dict[str, Any]:
    return {
        "key": lease.key,
        "key_hash": lease.key_hash,
        "tickets_consumed": lease.tickets_consumed,
        "expires_at": lease.expires_at,
        "expires_at_unix": lease.expires_at_unix,
        "station_id": lease.station_id,
        "station_url": lease.station_url,
        "station_recently_attested": lease.station_recently_attested,
        "station_signature": lease.station_signature,
        "org_signature": lease.org_signature,
    }


def _ticket_preview(ticket: Ticket, *, include_tokens: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "created_at": ticket.created_at,
        "consumed_at": ticket.consumed_at,
        "status": ticket.status,
    }
    if include_tokens:
        payload["finalized_ticket"] = ticket.finalized_ticket
    return payload


def _station_payload(station: StationInfo) -> dict[str, Any]:
    return {
        "station_id": station.station_id,
        "url": station.url,
        "models": station.models,
        "providers": station.providers,
        "last_seen_seconds_ago": station.last_seen_seconds_ago,
        "version": station.version,
    }


def _ticket_file_path(ticket_file: str | Path) -> Path:
    return Path(ticket_file)
