from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional


@dataclass
class Ticket:
    finalized_ticket: str
    blinded_request: str | None = None
    signed_response: str | None = None
    created_at: str | None = None
    consumed_at: str | None = None
    status: str | None = None

    def is_active(self) -> bool:
        status = (self.status or "").lower()
        if self.consumed_at:
            return False
        return status not in {"archived", "consumed", "used"}

    def archive(self, *, consumed_at: str | None = None, status: str = "consumed") -> None:
        self.consumed_at = consumed_at or datetime.now(timezone.utc).isoformat()
        self.status = status


@dataclass
class TicketExport:
    active: List[Ticket] = field(default_factory=list)
    archived: List[Ticket] = field(default_factory=list)

    def count_active(self) -> int:
        return len(self.active)


@dataclass
class KeyLease:
    key: str
    tickets_consumed: int
    station_id: str
    expires_at: str | None = None
    expires_at_unix: int | None = None
    key_hash: str | None = None
    station_url: str | None = None
    station_recently_attested: bool | None = None
    station_signature: str | None = None
    org_signature: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class TicketRedeemResult:
    tickets_issued: int
    expires_at: int | None
    public_key: str | None
    tickets: List[Ticket]


@dataclass
class OAResponse:
    response_id: str | None
    output_text: str | None
    raw: Mapping[str, Any]


@dataclass
class EphemeralInferenceResult:
    key_lease: KeyLease
    response: OAResponse


@dataclass
class StationInfo:
    station_id: str
    url: str
    models: List[str] = field(default_factory=list)
    providers: Mapping[str, Any] = field(default_factory=dict)
    last_seen_seconds_ago: int | None = None
    version: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


ModelTicketMap = Dict[str, int]
JSONMap = Dict[str, Any]
