from __future__ import annotations

from pathlib import Path

from ..config import OAConfig
from ..models import TicketExport, TicketRedeemResult
from ..transport import HTTPTransport
from .issuer import TicketIssuerService
from .parser import dump_ticket_export_file, load_ticket_export_file
from .store import TicketStore


class TicketService:
    def __init__(self, *, config: OAConfig, transport: HTTPTransport) -> None:
        self._config = config
        self._transport = transport

    def load_export(self, path: str | Path) -> TicketExport:
        return load_ticket_export_file(path)

    def save_export(self, path: str | Path, data: TicketExport) -> None:
        dump_ticket_export_file(path, data)

    def open_store(self, path: str | Path) -> TicketStore:
        return TicketStore.from_file(path)

    def redeem_code(
        self,
        *,
        credential: str,
        requested_count: int | None = None,
        store: TicketStore | None = None,
    ) -> TicketRedeemResult:
        issuer = TicketIssuerService(config=self._config, transport=self._transport)
        result = issuer.redeem_code(credential=credential, requested_count=requested_count)
        if store is not None:
            store.extend_active(result.tickets)
        return result
