from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class IdempotencyClass(str, Enum):
    IDEMPOTENT = "idempotent"
    SAFE_WITH_ROLLBACK = "safe_with_rollback"
    NON_IDEMPOTENT = "non_idempotent"


@dataclass(frozen=True)
class EndpointRetryPolicy:
    allow_retry: bool
    idempotency: IdempotencyClass
    rationale: str


RETRY_POLICY_MATRIX: Mapping[str, EndpointRetryPolicy] = {
    "model_tickets": EndpointRetryPolicy(
        allow_retry=True,
        idempotency=IdempotencyClass.IDEMPOTENT,
        rationale="Read-only GET request for model tier costs.",
    ),
    "online_stations": EndpointRetryPolicy(
        allow_retry=True,
        idempotency=IdempotencyClass.IDEMPOTENT,
        rationale="Read-only GET request for currently online stations.",
    ),
    "org_public_key": EndpointRetryPolicy(
        allow_retry=True,
        idempotency=IdempotencyClass.IDEMPOTENT,
        rationale="Read-only GET request for org verification key material.",
    ),
    "request_key": EndpointRetryPolicy(
        allow_retry=True,
        idempotency=IdempotencyClass.SAFE_WITH_ROLLBACK,
        rationale=(
            "Ticket spend happens server-side with rollback semantics on station relay failures; "
            "transient retries are acceptable."
        ),
    ),
    "ticket_issue_public_key": EndpointRetryPolicy(
        allow_retry=True,
        idempotency=IdempotencyClass.IDEMPOTENT,
        rationale="Read-only GET request for ticket issuer public key.",
    ),
    "alpha_register": EndpointRetryPolicy(
        allow_retry=False,
        idempotency=IdempotencyClass.NON_IDEMPOTENT,
        rationale="Blind-signature issuance request is non-idempotent and must not be retried blindly.",
    ),
    "inference": EndpointRetryPolicy(
        allow_retry=True,
        idempotency=IdempotencyClass.IDEMPOTENT,
        rationale="Inference calls are treated as retryable for transient transport and 5xx/429 failures.",
    ),
}


def endpoint_retry_allowed(endpoint: str) -> bool:
    policy = RETRY_POLICY_MATRIX.get(endpoint)
    if policy is None:
        raise ValueError(f"Unknown retry policy endpoint: {endpoint}")
    return policy.allow_retry
