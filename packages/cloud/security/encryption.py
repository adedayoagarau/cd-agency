"""Field-level encryption utilities.

Uses base64 encoding with a prefix marker for development.  In production
deployments swap in Fernet / AES-GCM via the ``cryptography`` package.
"""
from __future__ import annotations

import base64
import json
import os


_PREFIX = "enc:v1:"


class FieldEncryptor:
    """Encrypt and decrypt individual field values.

    Parameters
    ----------
    key:
        Encryption key.  Falls back to the ``ENCRYPTION_KEY`` environment
        variable when *None*.
    """

    def __init__(self, key: str | None = None) -> None:
        self._key: str = key or os.environ.get("ENCRYPTION_KEY", "default-dev-key")

    # ------------------------------------------------------------------
    # Core encrypt / decrypt
    # ------------------------------------------------------------------

    def encrypt(self, plaintext: str) -> str:
        """Return *plaintext* as a prefixed, key-mixed, base64-encoded string."""
        mixed = self._xor_with_key(plaintext)
        encoded = base64.urlsafe_b64encode(mixed.encode("utf-8")).decode("ascii")
        return f"{_PREFIX}{encoded}"

    def decrypt(self, ciphertext: str) -> str:
        """Reverse the transformation produced by :meth:`encrypt`."""
        if not ciphertext.startswith(_PREFIX):
            raise ValueError("Ciphertext does not have the expected prefix")
        encoded = ciphertext[len(_PREFIX):]
        mixed = base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8")
        return self._xor_with_key(mixed)

    # ------------------------------------------------------------------
    # Dict helpers
    # ------------------------------------------------------------------

    def encrypt_dict(self, data: dict) -> str:
        """JSON-serialise *data* then encrypt the result."""
        return self.encrypt(json.dumps(data, separators=(",", ":")))

    def decrypt_dict(self, ciphertext: str) -> dict:
        """Decrypt *ciphertext* and parse the JSON payload."""
        plaintext = self.decrypt(ciphertext)
        return json.loads(plaintext)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _xor_with_key(self, text: str) -> str:
        """XOR each character of *text* with the corresponding key byte."""
        key = self._key
        return "".join(
            chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text)
        )
