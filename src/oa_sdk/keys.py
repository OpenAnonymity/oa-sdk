from __future__ import annotations

from typing import Any, Mapping

from .auth import build_inference_ticket_header
from .config import OAConfig
from .errors import OAHTTPError, OAProtocolError, TicketUsedError
from .models import KeyLease, ModelTicketMap, StationInfo
from .retry_policy import endpoint_retry_allowed
from .signatures import RequestKeySignatureVerification, verify_request_key_signatures
from .tickets.store import Order, TicketStore
from .transport import HTTPTransport, ensure_success


class KeyService:
    def __init__(self, *, config: OAConfig, transport: HTTPTransport) -> None:
        self._config = config
        self._transport = transport

    def fetch_model_tickets(self) -> ModelTicketMap:
        url = f"{self._config.org_api_base}/chat/model-tickets"
        result = self._transport.request_json(
            "GET",
            url,
            allow_retry=endpoint_retry_allowed("model_tickets"),
            context="model tickets",
        )
        ensure_success(result, context="model tickets")

        if not isinstance(result.data, dict):
            raise OAProtocolError("model tickets response is not a mapping")

        tickets: ModelTicketMap = {}
        for model_id, cost in result.data.items():
            if isinstance(model_id, str) and isinstance(cost, int):
                tickets[model_id] = cost
        return tickets

    def fetch_online_stations(self, *, version: int = 2) -> list[StationInfo]:
        if version not in (1, 2):
            raise ValueError("version must be 1 or 2")

        endpoint = "/api/v2/online" if version == 2 else "/api/online"
        url = f"{self._config.org_api_base}{endpoint}"
        result = self._transport.request_json(
            "GET",
            url,
            allow_retry=endpoint_retry_allowed("online_stations"),
            context="online stations",
        )
        ensure_success(result, context="online stations")

        if not isinstance(result.data, dict):
            raise OAProtocolError("online stations response is not a mapping")

        stations: list[StationInfo] = []
        for station_id, payload in result.data.items():
            if not isinstance(station_id, str) or not station_id:
                continue
            if not isinstance(payload, dict):
                continue

            models_raw = payload.get("models")
            models = [model for model in models_raw if isinstance(model, str)] if isinstance(models_raw, list) else []

            providers = payload.get("providers")
            providers_map: Mapping[str, Any] = providers if isinstance(providers, dict) else {}

            last_seen = payload.get("last_seen_seconds_ago")
            last_seen_seconds_ago = last_seen if isinstance(last_seen, int) else None

            station_version = payload.get("version")
            parsed_version = station_version if isinstance(station_version, int) else None

            station_url = payload.get("url")
            parsed_url = station_url if isinstance(station_url, str) else ""

            stations.append(
                StationInfo(
                    station_id=station_id,
                    url=parsed_url,
                    models=models,
                    providers=providers_map,
                    last_seen_seconds_ago=last_seen_seconds_ago,
                    version=parsed_version,
                    raw=payload,
                )
            )

        return sorted(stations, key=lambda station: station.station_id)

    def request_key_from_tokens(
        self,
        *,
        tokens: list[str],
        name: str = "OA-SDK-Key",
        station_id: str | None = None,
    ) -> KeyLease:
        auth_header = build_inference_ticket_header(tokens)
        body: dict[str, Any] = {"name": name}
        if station_id:
            body["station_id"] = station_id

        url = f"{self._config.org_api_base}/api/request_key"
        result = self._transport.request_json(
            "POST",
            url,
            headers={
                "Authorization": auth_header,
                "Content-Type": "application/json",
            },
            json_body=body,
            allow_retry=endpoint_retry_allowed("request_key"),
            context="request key",
        )

        if not (200 <= result.status_code < 300):
            message = _extract_error_message(result.data, result.text, result.status_code)
            if _is_ticket_spent_error(result.status_code, message):
                raise TicketUsedError(message)
            raise OAHTTPError(result.status_code, message, detail=result.data)

        if not isinstance(result.data, dict):
            raise OAProtocolError("request key response is not a JSON object")

        key = result.data.get("key")
        station = result.data.get("station_id")
        if not isinstance(key, str) or not key:
            raise OAProtocolError("request key response missing 'key'")
        if not isinstance(station, str) or not station:
            raise OAProtocolError("request key response missing 'station_id'")

        tickets_consumed = result.data.get("tickets_consumed")
        if not isinstance(tickets_consumed, int):
            tickets_consumed = len(tokens)

        expires_at = result.data.get("expires_at")
        if not isinstance(expires_at, str):
            expires_at = None

        expires_at_unix = result.data.get("expires_at_unix")
        if not isinstance(expires_at_unix, int):
            expires_at_unix = None

        return KeyLease(
            key=key,
            key_hash=result.data.get("key_hash") if isinstance(result.data.get("key_hash"), str) else None,
            tickets_consumed=tickets_consumed,
            expires_at=expires_at,
            expires_at_unix=expires_at_unix,
            station_id=station,
            station_url=result.data.get("station_url") if isinstance(result.data.get("station_url"), str) else None,
            station_recently_attested=(
                result.data.get("station_recently_attested")
                if isinstance(result.data.get("station_recently_attested"), bool)
                else None
            ),
            station_signature=(
                result.data.get("station_signature")
                if isinstance(result.data.get("station_signature"), str)
                else None
            ),
            org_signature=(
                result.data.get("org_signature")
                if isinstance(result.data.get("org_signature"), str)
                else None
            ),
            raw=result.data,
        )

    def request_key_from_store(
        self,
        *,
        store: TicketStore,
        count: int = 1,
        name: str = "OA-SDK-Key",
        station_id: str | None = None,
        order: Order = "head",
        consume_on_ticket_used: bool = True,
    ) -> KeyLease:
        selected = store.select(count, order=order)
        tokens = selected.finalized_tokens()

        try:
            lease = self.request_key_from_tokens(tokens=tokens, name=name, station_id=station_id)
        except TicketUsedError:
            if consume_on_ticket_used:
                store.archive_selected(selected, status="used")
            raise

        store.archive_selected(selected, status="consumed")
        return lease

    def fetch_org_public_key(self) -> str:
        url = f"{self._config.org_api_base}/api/public_key"
        result = self._transport.request_json(
            "GET",
            url,
            allow_retry=endpoint_retry_allowed("org_public_key"),
            context="org public key",
        )
        ensure_success(result, context="org public key")

        if not isinstance(result.data, Mapping):
            raise OAProtocolError("org public key response is not an object")

        public_key = result.data.get("public_key")
        if not isinstance(public_key, str) or not public_key:
            raise OAProtocolError("org public key response missing 'public_key'")

        return public_key

    def verify_key_lease_signatures(
        self,
        *,
        lease: KeyLease,
        station_public_key_hex: str | None = None,
        org_public_key_hex: str | None = None,
    ) -> RequestKeySignatureVerification:
        return verify_request_key_signatures(
            lease=lease,
            station_public_key_hex=station_public_key_hex,
            org_public_key_hex=org_public_key_hex,
        )


def _extract_error_message(data: object, text: str, status_code: int) -> str:
    if isinstance(data, Mapping):
        for key in ("detail", "error", "message"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value
    if text:
        return text
    return f"HTTP {status_code}"


def _is_ticket_spent_error(status_code: int, message: str) -> bool:
    lower = message.lower()
    if status_code == 401:
        return True
    spent_markers = ("double", "spent", "used", "already")
    return any(marker in lower for marker in spent_markers)
