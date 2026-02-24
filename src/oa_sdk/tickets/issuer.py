from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from ..config import OAConfig
from ..errors import BlindSignatureUnavailableError, OAProtocolError
from ..models import Ticket, TicketRedeemResult
from ..transport import HTTPTransport, ensure_success

DEFAULT_CHALLENGE_ISSUER = (
    "if you found this, email hi@openanonymity.ai with code OA-BLIND-2026 -- we need you :D"
)


class PrivacyPassTokenClient:
    def __init__(self) -> None:
        try:
            import privacypass_py as pp  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on local install
            raise BlindSignatureUnavailableError(
                "privacypass-py is required for ticket issuance. Install with extras: "
                "pip install oa-sdk[blind-signatures]"
            ) from exc

        self._pp = pp
        self._client = pp.TokenClient()

    def create_blinded_requests(
        self,
        *,
        public_key: str,
        count: int,
    ) -> Tuple[List[Tuple[int, str]], Dict[int, str]]:
        if count <= 0:
            raise ValueError("count must be positive")

        challenge = self._pp.TokenChallenge.create(
            issuer_name=DEFAULT_CHALLENGE_ISSUER,
            origin_info=[],
            redemption_context=None,
        )

        blinded: List[Tuple[int, str]] = []
        state_ids: Dict[int, str] = {}

        for index in range(count):
            request_b64, state_id = self._client.create_token_request(public_key, challenge)
            blinded.append((index, request_b64))
            state_ids[index] = state_id

        return blinded, state_ids

    def finalize_signed_responses(
        self,
        *,
        signed_responses: List[Tuple[int, str]],
        state_ids: Dict[int, str],
    ) -> List[Ticket]:
        response_by_index = {index: value for index, value in signed_responses}
        created_at = datetime.now(timezone.utc).isoformat()

        tickets: List[Ticket] = []
        for index in sorted(state_ids):
            state_id = state_ids[index]
            signed = response_by_index.get(index)
            if signed is None:
                raise OAProtocolError(f"Missing signed response for ticket index {index}")

            token = self._client.finalize_token(signed, state_id)
            tickets.append(
                Ticket(
                    finalized_ticket=token,
                    signed_response=signed,
                    created_at=created_at,
                )
            )
        return tickets


class TicketIssuerService:
    def __init__(self, *, config: OAConfig, transport: HTTPTransport) -> None:
        self._config = config
        self._transport = transport
        self._privacy_pass = PrivacyPassTokenClient()

    def fetch_public_key(self) -> str:
        url = f"{self._config.org_api_base}/api/ticket/issue/public-key"
        result = self._transport.request_json("GET", url, context="ticket issue public key")
        ensure_success(result, context="ticket issue public key")

        if not isinstance(result.data, dict) or not isinstance(result.data.get("public_key"), str):
            raise OAProtocolError("Public key response missing 'public_key'")
        return result.data["public_key"]

    def redeem_code(
        self,
        *,
        credential: str,
        requested_count: Optional[int] = None,
    ) -> TicketRedeemResult:
        count = requested_count or infer_ticket_count_from_code(credential)
        if count is None:
            raise ValueError(
                "Unable to infer ticket count from credential. Provide requested_count explicitly."
            )

        public_key = self.fetch_public_key()
        blinded_requests, state_ids = self._privacy_pass.create_blinded_requests(
            public_key=public_key,
            count=count,
        )

        url = f"{self._config.org_api_base}/api/alpha-register"
        result = self._transport.request_json(
            "POST",
            url,
            headers={"Content-Type": "application/json"},
            json_body={
                "credential": credential,
                "blinded_requests": blinded_requests,
            },
            allow_retry=False,
            context="alpha register",
        )
        ensure_success(result, context="alpha register")

        if not isinstance(result.data, dict):
            raise OAProtocolError("alpha register response is not an object")

        signed_responses = result.data.get("signed_responses")
        if not isinstance(signed_responses, list):
            raise OAProtocolError("alpha register response missing signed_responses")

        parsed_signed: List[Tuple[int, str]] = []
        for pair in signed_responses:
            if not isinstance(pair, list | tuple) or len(pair) != 2:
                continue
            index, response_b64 = pair
            if isinstance(index, int) and isinstance(response_b64, str):
                parsed_signed.append((index, response_b64))

        tickets = self._privacy_pass.finalize_signed_responses(
            signed_responses=parsed_signed,
            state_ids=state_ids,
        )

        return TicketRedeemResult(
            tickets_issued=len(tickets),
            expires_at=result.data.get("expires_at") if isinstance(result.data.get("expires_at"), int) else None,
            public_key=result.data.get("public_key") if isinstance(result.data.get("public_key"), str) else None,
            tickets=tickets,
        )


def infer_ticket_count_from_code(credential: str) -> int | None:
    if len(credential) < 4:
        return None
    suffix = credential[-4:]
    try:
        value = int(suffix, 16)
    except ValueError:
        return None
    if value <= 0:
        return None
    return value
