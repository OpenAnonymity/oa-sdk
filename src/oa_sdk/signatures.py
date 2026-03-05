from __future__ import annotations

from dataclasses import dataclass

from .errors import OAProtocolError, OptionalDependencyError
from .models import KeyLease


@dataclass(frozen=True)
class RequestKeySignatureVerification:
    station_signature_valid: bool | None
    org_signature_valid: bool | None


def build_station_signature_payload(*, station_id: str, key: str, expires_at_unix: int) -> str:
    return f"{station_id}|{key}|{expires_at_unix}"


def build_org_signature_payload(
    *,
    station_id: str,
    key: str,
    expires_at_unix: int,
    station_signature: str,
) -> str:
    return f"{station_id}|{key}|{expires_at_unix}|{station_signature}"


def verify_request_key_signatures(
    *,
    lease: KeyLease,
    station_public_key_hex: str | None = None,
    org_public_key_hex: str | None = None,
) -> RequestKeySignatureVerification:
    expires_at_unix = lease.expires_at_unix
    if not isinstance(expires_at_unix, int):
        raise OAProtocolError("Key lease is missing integer 'expires_at_unix' required for signature checks")

    station_signature_valid: bool | None = None
    if station_public_key_hex is not None:
        if not lease.station_signature:
            raise OAProtocolError("Key lease is missing station_signature")
        station_payload = build_station_signature_payload(
            station_id=lease.station_id,
            key=lease.key,
            expires_at_unix=expires_at_unix,
        )
        station_signature_valid = verify_ed25519_signature(
            message=station_payload,
            signature_hex=lease.station_signature,
            public_key_hex=station_public_key_hex,
        )

    org_signature_valid: bool | None = None
    if org_public_key_hex is not None:
        if not lease.org_signature:
            raise OAProtocolError("Key lease is missing org_signature")
        if not lease.station_signature:
            raise OAProtocolError("Key lease is missing station_signature required for org signature payload")
        org_payload = build_org_signature_payload(
            station_id=lease.station_id,
            key=lease.key,
            expires_at_unix=expires_at_unix,
            station_signature=lease.station_signature,
        )
        org_signature_valid = verify_ed25519_signature(
            message=org_payload,
            signature_hex=lease.org_signature,
            public_key_hex=org_public_key_hex,
        )

    return RequestKeySignatureVerification(
        station_signature_valid=station_signature_valid,
        org_signature_valid=org_signature_valid,
    )


def verify_ed25519_signature(*, message: str | bytes, signature_hex: str, public_key_hex: str) -> bool:
    message_bytes = message.encode("utf-8") if isinstance(message, str) else message
    signature = _decode_hex("signature", signature_hex, expected_bytes=64)
    public_key = _decode_hex("public_key", public_key_hex, expected_bytes=32)

    for verifier in (_verify_with_nacl, _verify_with_cryptography):
        verdict = verifier(message_bytes, signature, public_key)
        if verdict is not None:
            return verdict

    raise OptionalDependencyError(
        "Ed25519 verification requires optional dependency 'pynacl' or 'cryptography'. "
        "Install one of: pip install pynacl  OR  pip install cryptography"
    )


def _decode_hex(label: str, value: str, *, expected_bytes: int) -> bytes:
    if not isinstance(value, str) or not value:
        raise OAProtocolError(f"{label} must be a non-empty hex string")
    if len(value) % 2 != 0:
        raise OAProtocolError(f"{label} must be valid even-length hex")
    try:
        decoded = bytes.fromhex(value)
    except ValueError as exc:
        raise OAProtocolError(f"{label} must be valid hex") from exc
    if len(decoded) != expected_bytes:
        raise OAProtocolError(f"{label} must be {expected_bytes} bytes")
    return decoded


def _verify_with_nacl(message: bytes, signature: bytes, public_key: bytes) -> bool | None:
    try:
        from nacl.exceptions import BadSignatureError
        from nacl.signing import VerifyKey
    except ImportError:
        return None

    try:
        VerifyKey(public_key).verify(message, signature)
    except BadSignatureError:
        return False
    return True


def _verify_with_cryptography(message: bytes, signature: bytes, public_key: bytes) -> bool | None:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        return None

    key = Ed25519PublicKey.from_public_bytes(public_key)
    try:
        key.verify(signature, message)
    except InvalidSignature:
        return False
    return True
