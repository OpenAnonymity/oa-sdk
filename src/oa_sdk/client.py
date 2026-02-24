from __future__ import annotations

from .config import OAConfig
from .inference.models import AccessCredential, ResponseRequest
from .inference.service import InferenceService
from .keys import KeyService
from .models import EphemeralInferenceResult
from .tickets.service import TicketService
from .tickets.store import TicketStore
from .transport import HTTPTransport


class OAClient:
    def __init__(self, config: OAConfig | None = None) -> None:
        self.config = config or OAConfig()
        self._transport = HTTPTransport(
            timeout_seconds=self.config.timeout_seconds,
            retry=self.config.retry,
        )
        self.tickets = TicketService(config=self.config, transport=self._transport)
        self.keys = KeyService(config=self.config, transport=self._transport)
        self.inference = InferenceService(config=self.config, transport=self._transport)

    def get_ticket_cost_for_model(self, model_id: str, *, fallback: int = 1) -> int:
        model_tickets = self.keys.fetch_model_tickets()
        cost = model_tickets.get(model_id, fallback)
        return cost if cost > 0 else fallback

    def request_key_and_infer_openrouter(
        self,
        *,
        store: TicketStore,
        request: ResponseRequest,
        ticket_count: int | None = None,
        key_name: str = "OA-SDK-Key",
        station_id: str | None = None,
    ) -> EphemeralInferenceResult:
        resolved_count = ticket_count or self.get_ticket_cost_for_model(request.model)

        lease = self.keys.request_key_from_store(
            store=store,
            count=resolved_count,
            name=key_name,
            station_id=station_id,
        )

        backend = self.inference.openrouter_ephemeral_backend()
        response = self.inference.create_response(
            request,
            backend=backend,
            credential=AccessCredential(token=lease.key),
        )

        return EphemeralInferenceResult(key_lease=lease, response=response)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> OAClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()
