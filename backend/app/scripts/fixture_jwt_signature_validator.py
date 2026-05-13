from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.local_jwks_fixture_validator import select_local_jwk_by_kid


SHA256_DIGESTINFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


@dataclass(frozen=True)
class FixtureJWTValidationFailure:
    code: str
    detail: str


@dataclass(frozen=True)
class FixtureJWTValidationResult:
    status: str
    header: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    failures: list[FixtureJWTValidationFailure] = field(default_factory=list)
    authorization_allowed: bool = False


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode((value + "=" * (-len(value) % 4)).encode("ascii"))


def _decode_json_segment(value: str) -> dict[str, Any]:
    decoded = json.loads(_b64url_decode(value).decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("JWT segment must decode to an object.")
    return decoded


def _int_from_b64url(value: str) -> int:
    return int.from_bytes(_b64url_decode(value), "big")


def _verify_rs256_pkcs1_v1_5(signing_input: bytes, signature: bytes, *, n: int, e: int) -> bool:
    if n <= 0 or e <= 1:
        return False
    key_bytes = (n.bit_length() + 7) // 8
    if len(signature) != key_bytes:
        return False
    signature_int = int.from_bytes(signature, "big")
    encoded = pow(signature_int, e, n).to_bytes(key_bytes, "big")
    digest = hashlib.sha256(signing_input).digest()
    expected_tail = SHA256_DIGESTINFO_PREFIX + digest
    if len(encoded) < len(expected_tail) + 11:
        return False
    if not encoded.startswith(b"\x00\x01"):
        return False
    separator_index = encoded.find(b"\x00", 2)
    if separator_index < 10:
        return False
    padding = encoded[2:separator_index]
    if any(byte != 0xFF for byte in padding):
        return False
    return encoded[separator_index + 1 :] == expected_tail


def validate_fixture_jwt_signature(token: str, *, jwks_path: Path) -> FixtureJWTValidationResult:
    parts = token.split(".")
    if len(parts) != 3:
        return FixtureJWTValidationResult(
            status="ERROR",
            failures=[FixtureJWTValidationFailure("JWT_MALFORMED", "JWT must have three segments.")],
        )
    try:
        header = _decode_json_segment(parts[0])
        payload = _decode_json_segment(parts[1])
    except Exception as exc:
        return FixtureJWTValidationResult(
            status="ERROR",
            failures=[FixtureJWTValidationFailure("JWT_SEGMENT_DECODE_FAILED", str(exc))],
        )

    if header.get("alg") != "RS256":
        return FixtureJWTValidationResult(
            status="ERROR",
            header=header,
            payload=payload,
            failures=[FixtureJWTValidationFailure("JWT_ALG_UNSUPPORTED", "Fixture validator accepts RS256 only.")],
        )
    kid = str(header.get("kid") or "").strip()
    selected = select_local_jwk_by_kid(jwks_path, kid=kid)
    if selected.status != "OK" or not selected.key:
        return FixtureJWTValidationResult(
            status="ERROR",
            header=header,
            payload=payload,
            failures=[FixtureJWTValidationFailure(failure.code, failure.detail) for failure in selected.failures],
        )

    try:
        n = _int_from_b64url(str(selected.key.get("n") or ""))
        e = _int_from_b64url(str(selected.key.get("e") or ""))
        signature = _b64url_decode(parts[2])
    except Exception as exc:
        return FixtureJWTValidationResult(
            status="ERROR",
            header=header,
            payload=payload,
            failures=[FixtureJWTValidationFailure("JWT_KEY_OR_SIGNATURE_DECODE_FAILED", str(exc))],
        )

    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    if not _verify_rs256_pkcs1_v1_5(signing_input, signature, n=n, e=e):
        return FixtureJWTValidationResult(
            status="ERROR",
            header=header,
            payload=payload,
            failures=[FixtureJWTValidationFailure("JWT_SIGNATURE_INVALID", "Fixture JWT signature did not verify.")],
        )

    return FixtureJWTValidationResult(status="OK", header=header, payload=payload, authorization_allowed=False)
