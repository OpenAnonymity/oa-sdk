from __future__ import annotations

from typing import Iterable, List

from .errors import TicketFormatError


def build_inference_ticket_header(tokens: Iterable[str]) -> str:
    normalized = [token.strip() for token in tokens if token and token.strip()]
    if not normalized:
        raise TicketFormatError("At least one ticket token is required")

    joined = ",".join(normalized)
    if len(normalized) == 1:
        return f"InferenceTicket token={joined}"
    return f"InferenceTicket tokens={joined}"


def parse_inference_ticket_header(authorization: str) -> List[str]:
    if not authorization.startswith("InferenceTicket"):
        raise TicketFormatError("Invalid authorization scheme")

    if "tokens=" in authorization:
        raw = authorization.replace("InferenceTicket tokens=", "", 1)
    elif "token=" in authorization:
        raw = authorization.replace("InferenceTicket token=", "", 1)
    else:
        raise TicketFormatError("Missing token/tokens field")

    values = [token.strip() for token in raw.split(",") if token.strip()]
    if not values:
        raise TicketFormatError("No ticket tokens found")
    return values
