from __future__ import annotations


class OAError(Exception):
    """Base SDK error."""


class OAProtocolError(OAError):
    """Unexpected remote payload or protocol mismatch."""


class OAHTTPError(OAError):
    """HTTP request failed."""

    def __init__(self, status_code: int, message: str, *, detail: object | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class OARetryExhaustedError(OAError):
    """Transport retries exhausted."""


class TicketError(OAError):
    """Base ticket error."""


class InsufficientTicketsError(TicketError):
    """Not enough tickets available."""


class TicketUsedError(TicketError):
    """Ticket has already been spent / double-used."""


class TicketFormatError(TicketError):
    """Ticket payload parsing failed."""


class BlindSignatureUnavailableError(TicketError):
    """privacypass-py or blind-signature dependencies unavailable."""


class BackendError(OAError):
    """Inference backend call failed."""


class OptionalDependencyError(OAError):
    """An optional dependency required for this feature is not installed."""
