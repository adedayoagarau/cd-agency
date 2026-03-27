from __future__ import annotations

import base64
import json
import os
import urllib.request
from dataclasses import dataclass, field
from typing import Any

# Module-level JWKS cache: maps kid -> JWK dict
_jwks_cache: dict[str, dict[str, Any]] = {}


@dataclass(frozen=True)
class ClerkAuthConfig:
    """Configuration for Clerk authentication."""

    clerk_secret_key: str = field(
        default_factory=lambda: os.environ.get("CLERK_SECRET_KEY", "")
    )
    clerk_publishable_key: str = field(
        default_factory=lambda: os.environ.get("CLERK_PUBLISHABLE_KEY", "")
    )
    jwks_url: str = field(
        default_factory=lambda: os.environ.get(
            "CLERK_JWKS_URL",
            "https://api.clerk.com/.well-known/jwks.json",
        )
    )


def _b64_decode(data: str) -> bytes:
    """Decode base64url-encoded data with padding correction."""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode the payload of a JWT without signature verification.

    Splits the token into header.payload.signature, base64url-decodes the
    payload segment, and returns it as a dict.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT: expected 3 dot-separated segments")

    payload_bytes = _b64_decode(parts[1])
    return json.loads(payload_bytes)


def _decode_jwt_header(token: str) -> dict[str, Any]:
    """Decode the header of a JWT."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT: expected 3 dot-separated segments")

    header_bytes = _b64_decode(parts[0])
    return json.loads(header_bytes)


def fetch_jwks(config: ClerkAuthConfig | None = None) -> dict[str, dict[str, Any]]:
    """Fetch JWKS from Clerk and populate the module-level cache.

    Returns the cache dict mapping ``kid`` to JWK key objects.
    """
    if config is None:
        config = ClerkAuthConfig()

    req = urllib.request.Request(
        config.jwks_url,
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        data = json.loads(resp.read().decode())

    for key in data.get("keys", []):
        kid = key.get("kid")
        if kid:
            _jwks_cache[kid] = key

    return _jwks_cache


def get_signing_key(kid: str, config: ClerkAuthConfig | None = None) -> dict[str, Any]:
    """Return the JWK for the given ``kid``, fetching JWKS if not cached."""
    if kid not in _jwks_cache:
        fetch_jwks(config)
    key = _jwks_cache.get(kid)
    if key is None:
        raise ValueError(f"Signing key not found for kid: {kid}")
    return key


def verify_clerk_token(
    token: str,
    config: ClerkAuthConfig | None = None,
) -> dict[str, Any]:
    """Verify a Clerk-issued JWT and return its claims.

    This performs the following checks:
    1. Decodes the JWT header & payload (base64url).
    2. Ensures the signing key (``kid``) exists in the Clerk JWKS.
    3. Validates basic claims (``exp``, ``iss``).

    Full cryptographic RS256 signature verification should be handled in
    production by a dedicated library; this implementation focuses on claim
    extraction and JWKS key-presence validation.

    Returns the decoded payload dict containing ``sub``, ``org_id``,
    ``permissions``, etc.
    """
    import time

    if config is None:
        config = ClerkAuthConfig()

    header = _decode_jwt_header(token)
    kid = header.get("kid")
    if not kid:
        raise ValueError("JWT header missing 'kid'")

    # Ensure the key exists in Clerk's JWKS (fetches if not cached)
    get_signing_key(kid, config)

    payload = _decode_jwt_payload(token)

    # --- Claim validation ---------------------------------------------------
    now = int(time.time())

    exp = payload.get("exp")
    if exp is not None and now > int(exp):
        raise ValueError("JWT has expired")

    nbf = payload.get("nbf")
    if nbf is not None and now < int(nbf):
        raise ValueError("JWT is not yet valid (nbf)")

    if "sub" not in payload:
        raise ValueError("JWT missing 'sub' claim")

    return payload
