from __future__ import annotations

from typing import Iterable, List

from .errors import TicketFormatError


def build_inference_ticket_header(tokens: Iterable[str]) -> str:
    normalized = [_normalize_ticket_token(token) for token in tokens if token and token.strip()]
    if not normalized:
        raise TicketFormatError("At least one ticket token is required")

    joined = ",".join(normalized)
    if len(normalized) == 1:
        return f"InferenceTicket token={joined}"
    return f"InferenceTicket tokens={joined}"


def parse_inference_ticket_header(authorization: str) -> List[str]:
    prefix = "InferenceTicket "
    if not authorization.startswith(prefix):
        raise TicketFormatError("Invalid authorization scheme")

    payload = authorization[len(prefix):]
    if payload.startswith("tokens="):
        raw = payload[len("tokens=") :]
    elif payload.startswith("token="):
        raw = payload[len("token=") :]
    else:
        raise TicketFormatError("Missing token/tokens field")

    values = [_normalize_ticket_token(token) for token in raw.split(",") if token.strip()]
    if not values:
        raise TicketFormatError("No ticket tokens found")
    return values


def _normalize_ticket_token(token: str) -> str:
    normalized = token.strip()
    if not normalized:
        raise TicketFormatError("Ticket token cannot be empty")
    if any(character in normalized for character in (",", "\r", "\n")):
        raise TicketFormatError("Ticket token contains invalid delimiter characters")
    if any(character.isspace() for character in normalized):
        raise TicketFormatError("Ticket token contains whitespace")
    return normalized
