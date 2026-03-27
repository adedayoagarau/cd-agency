from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

_PREFIX_LENGTH = 8
_SECRET_LENGTH = 32
_API_KEY_PREFIX = "cda"


@dataclass
class APIKey:
    """Represents a stored API key record."""

    id: int
    org_id: str
    prefix: str
    key_hash: str
    name: str
    scopes: list[str]
    created_by: str
    is_active: bool = True


def _hash_secret(secret: str) -> str:
    """Return a SHA-256 hex digest of the secret portion of an API key."""
    return hashlib.sha256(secret.encode()).hexdigest()


def parse_api_key(key: str) -> tuple[str, str]:
    """Split a full API key into ``(prefix, secret)``.

    Expected format: ``cda_{prefix}_{secret}`` where *prefix* is 8 characters
    and *secret* is 32 characters.

    Raises ``ValueError`` if the key does not match the expected format.
    """
    parts = key.split("_")
    if len(parts) != 3 or parts[0] != _API_KEY_PREFIX:
        raise ValueError(
            f"Invalid API key format. Expected '{_API_KEY_PREFIX}_<prefix>_<secret>'"
        )

    prefix, secret = parts[1], parts[2]

    if len(prefix) != _PREFIX_LENGTH:
        raise ValueError(f"API key prefix must be {_PREFIX_LENGTH} characters")
    if len(secret) != _SECRET_LENGTH:
        raise ValueError(f"API key secret must be {_SECRET_LENGTH} characters")

    return prefix, secret


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key.

    Returns:
        A 3-tuple of ``(full_key, prefix, key_hash)`` where *full_key* is the
        string to give to the user (shown once), *prefix* is the public
        identifier stored alongside the hash, and *key_hash* is the SHA-256
        hex digest of the secret portion.
    """
    prefix = secrets.token_hex(_PREFIX_LENGTH // 2)  # 4 bytes → 8 hex chars
    secret = secrets.token_hex(_SECRET_LENGTH // 2)  # 16 bytes → 32 hex chars
    full_key = f"{_API_KEY_PREFIX}_{prefix}_{secret}"
    key_hash = _hash_secret(secret)
    return full_key, prefix, key_hash


def verify_api_key(key: str, session: Any) -> APIKey | None:
    """Look up an API key by prefix and verify its hash.

    Args:
        key: The full API key string (``cda_<prefix>_<secret>``).
        session: A SQLAlchemy-compatible session with an ``execute`` method.

    Returns:
        An :class:`APIKey` instance if valid, or ``None`` if not found / hash
        mismatch / inactive.
    """
    try:
        prefix, secret = parse_api_key(key)
    except ValueError:
        return None

    secret_hash = _hash_secret(secret)

    # Use a text query to stay ORM-agnostic; callers can adapt as needed.
    from sqlalchemy import text

    row = session.execute(
        text(
            "SELECT id, org_id, prefix, key_hash, name, scopes, created_by, is_active "
            "FROM api_keys WHERE prefix = :prefix LIMIT 1"
        ),
        {"prefix": prefix},
    ).fetchone()

    if row is None:
        return None

    record = APIKey(
        id=row[0],
        org_id=row[1],
        prefix=row[2],
        key_hash=row[3],
        name=row[4],
        scopes=row[5] if isinstance(row[5], list) else [],
        created_by=row[6],
        is_active=row[7],
    )

    if not record.is_active:
        return None

    if not secrets.compare_digest(record.key_hash, secret_hash):
        return None

    return record
