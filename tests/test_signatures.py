from __future__ import annotations

import pytest

from oa_sdk.errors import OAProtocolError, OptionalDependencyError
from oa_sdk.models import KeyLease
from oa_sdk.signatures import (
    build_org_signature_payload,
    build_station_signature_payload,
    verify_ed25519_signature,
    verify_request_key_signatures,
)


def _sample_lease() -> KeyLease:
    return KeyLease(
        key="key-123",
        tickets_consumed=1,
        station_id="station-a",
        expires_at_unix=1735689600,
        station_signature="ab" * 64,
        org_signature="cd" * 64,
    )


def test_payload_builders_match_contract() -> None:
    station_payload = build_station_signature_payload(
        station_id="station-a",
        key="key-123",
        expires_at_unix=1735689600,
    )
    org_payload = build_org_signature_payload(
        station_id="station-a",
        key="key-123",
        expires_at_unix=1735689600,
        station_signature="ab" * 64,
    )

    assert station_payload == "station-a|key-123|1735689600"
    assert org_payload == f"station-a|key-123|1735689600|{'ab' * 64}"


def test_verify_request_key_signatures_uses_expected_payloads(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, str]] = []

    def fake_verify_ed25519_signature(*, message: str | bytes, signature_hex: str, public_key_hex: str) -> bool:
        rendered = message.decode("utf-8") if isinstance(message, bytes) else message
        calls.append((rendered, signature_hex, public_key_hex))
        return True

    monkeypatch.setattr("oa_sdk.signatures.verify_ed25519_signature", fake_verify_ed25519_signature)

    result = verify_request_key_signatures(
        lease=_sample_lease(),
        station_public_key_hex="11" * 32,
        org_public_key_hex="22" * 32,
    )

    assert result.station_signature_valid is True
    assert result.org_signature_valid is True
    assert calls == [
        ("station-a|key-123|1735689600", "ab" * 64, "11" * 32),
        (f"station-a|key-123|1735689600|{'ab' * 64}", "cd" * 64, "22" * 32),
    ]


def test_verify_request_key_signatures_requires_expires_at_unix() -> None:
    lease = KeyLease(
        key="key-123",
        tickets_consumed=1,
        station_id="station-a",
        expires_at_unix=None,
    )

    with pytest.raises(OAProtocolError):
        verify_request_key_signatures(lease=lease, station_public_key_hex="11" * 32)


def test_verify_ed25519_signature_rejects_invalid_hex() -> None:
    with pytest.raises(OAProtocolError):
        verify_ed25519_signature(
            message="hello",
            signature_hex="not-hex",
            public_key_hex="11" * 32,
        )


def test_verify_ed25519_signature_requires_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("oa_sdk.signatures._verify_with_nacl", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("oa_sdk.signatures._verify_with_cryptography", lambda *_args, **_kwargs: None)

    with pytest.raises(OptionalDependencyError):
        verify_ed25519_signature(
            message="hello",
            signature_hex="aa" * 64,
            public_key_hex="bb" * 32,
        )
