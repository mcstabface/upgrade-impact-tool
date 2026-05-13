from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_ACCEPTED_ALGORITHMS = ("RS256",)


@dataclass(frozen=True)
class JWKSValidationFailure:
    code: str
    detail: str


@dataclass(frozen=True)
class JWKSValidationResult:
    status: str
    key_count: int
    kids: list[str]
    failures: list[JWKSValidationFailure] = field(default_factory=list)
    authorization_allowed: bool = False


@dataclass(frozen=True)
class JWKSelectionResult:
    status: str
    kid: str
    key: dict[str, Any] | None = None
    failures: list[JWKSValidationFailure] = field(default_factory=list)
    authorization_allowed: bool = False


def load_local_jwks_fixture(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Local JWKS fixture not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JWKS fixture must be a JSON object.")
    return payload


def validate_local_jwks_fixture(
    path: Path,
    *,
    accepted_algorithms: tuple[str, ...] = DEFAULT_ACCEPTED_ALGORITHMS,
    require_kid: bool = True,
) -> JWKSValidationResult:
    jwks = load_local_jwks_fixture(path)
    failures: list[JWKSValidationFailure] = []
    keys = jwks.get("keys")
    if not isinstance(keys, list):
        return JWKSValidationResult("ERROR", 0, [], [JWKSValidationFailure("JWKS_KEYS_NOT_LIST", "JWKS keys must be a list.")])
    if not keys:
        failures.append(JWKSValidationFailure("JWKS_KEYS_EMPTY", "JWKS keys must not be empty."))

    kids: list[str] = []
    seen_kids: set[str] = set()
    for index, key in enumerate(keys):
        if not isinstance(key, dict):
            failures.append(JWKSValidationFailure("JWKS_KEY_NOT_OBJECT", f"keys[{index}] must be an object."))
            continue
        kid = str(key.get("kid") or "").strip()
        if require_kid and not kid:
            failures.append(JWKSValidationFailure("JWKS_KID_MISSING", f"keys[{index}] is missing kid."))
        if kid:
            if kid in seen_kids:
                failures.append(JWKSValidationFailure("JWKS_KID_DUPLICATE", f"Duplicate kid: {kid}."))
            seen_kids.add(kid)
            kids.append(kid)
        if str(key.get("kty") or "") != "RSA":
            failures.append(JWKSValidationFailure("JWKS_KTY_UNSUPPORTED", f"keys[{index}] must use kty RSA."))
        if str(key.get("use") or "sig") != "sig":
            failures.append(JWKSValidationFailure("JWKS_USE_UNSUPPORTED", f"keys[{index}] must use sig."))
        if str(key.get("alg") or "") not in accepted_algorithms:
            failures.append(JWKSValidationFailure("JWKS_ALG_UNSUPPORTED", f"keys[{index}] uses unsupported alg."))
        if not isinstance(key.get("n"), str) or not str(key.get("n") or "").strip():
            failures.append(JWKSValidationFailure("JWKS_RSA_PARAMETER_MISSING", f"keys[{index}] missing n."))
        if not isinstance(key.get("e"), str) or not str(key.get("e") or "").strip():
            failures.append(JWKSValidationFailure("JWKS_RSA_PARAMETER_MISSING", f"keys[{index}] missing e."))

    return JWKSValidationResult("ERROR" if failures else "OK", len(keys), kids, failures, False)


def select_local_jwk_by_kid(
    path: Path,
    *,
    kid: str,
    accepted_algorithms: tuple[str, ...] = DEFAULT_ACCEPTED_ALGORITHMS,
    require_kid: bool = True,
) -> JWKSelectionResult:
    selected_kid = kid.strip()
    if require_kid and not selected_kid:
        return JWKSelectionResult("ERROR", selected_kid, None, [JWKSValidationFailure("JWKS_KID_REQUIRED_FOR_SELECTION", "kid is required.")])

    validation = validate_local_jwks_fixture(path, accepted_algorithms=accepted_algorithms, require_kid=require_kid)
    if validation.status != "OK":
        return JWKSelectionResult("ERROR", selected_kid, None, validation.failures)

    keys = load_local_jwks_fixture(path).get("keys") or []
    for key in keys:
        if isinstance(key, dict) and str(key.get("kid") or "") == selected_kid:
            return JWKSelectionResult("OK", selected_kid, key, [], False)
    return JWKSelectionResult("ERROR", selected_kid, None, [JWKSValidationFailure("JWKS_KEY_NOT_FOUND", f"No key found for kid: {selected_kid}.")])
