"""Tests for security module — encryption, rate limiting, sanitization."""
from __future__ import annotations

import time

import pytest


# ---------------------------------------------------------------------------
# Encryption
# ---------------------------------------------------------------------------


class TestFieldEncryptor:
    def test_encrypt_decrypt_roundtrip(self):
        from packages.cloud.security.encryption import FieldEncryptor

        enc = FieldEncryptor(key="test-key-12345")
        plaintext = "Hello, World!"
        ciphertext = enc.encrypt(plaintext)
        assert ciphertext != plaintext
        assert ciphertext.startswith("enc:v1:")
        assert enc.decrypt(ciphertext) == plaintext

    def test_encrypt_produces_different_prefix(self):
        from packages.cloud.security.encryption import FieldEncryptor

        enc = FieldEncryptor(key="key1")
        ct = enc.encrypt("test")
        assert ct.startswith("enc:v1:")

    def test_decrypt_wrong_key_fails(self):
        from packages.cloud.security.encryption import FieldEncryptor

        enc1 = FieldEncryptor(key="key1")
        enc2 = FieldEncryptor(key="key2")
        ciphertext = enc1.encrypt("secret")
        # XOR with different key will produce garbage, not the original
        assert enc2.decrypt(ciphertext) != "secret"

    def test_decrypt_without_prefix_raises(self):
        from packages.cloud.security.encryption import FieldEncryptor

        enc = FieldEncryptor(key="key")
        with pytest.raises(ValueError, match="prefix"):
            enc.decrypt("not-encrypted-text")

    def test_encrypt_dict_roundtrip(self):
        from packages.cloud.security.encryption import FieldEncryptor

        enc = FieldEncryptor(key="dict-key")
        data = {"api_key": "sk-123", "secret": "abc"}
        ciphertext = enc.encrypt_dict(data)
        assert isinstance(ciphertext, str)
        result = enc.decrypt_dict(ciphertext)
        assert result == data

    def test_encrypt_empty_string(self):
        from packages.cloud.security.encryption import FieldEncryptor

        enc = FieldEncryptor(key="key")
        ct = enc.encrypt("")
        assert enc.decrypt(ct) == ""

    def test_encrypt_unicode(self):
        from packages.cloud.security.encryption import FieldEncryptor

        enc = FieldEncryptor(key="key")
        plaintext = "Hello 🌍 café"
        ct = enc.encrypt(plaintext)
        assert enc.decrypt(ct) == plaintext


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------


class TestInMemoryRateLimiter:
    def test_allows_under_limit(self):
        from packages.cloud.security.rate_limiter import InMemoryRateLimiter

        limiter = InMemoryRateLimiter(requests_per_minute=5, requests_per_hour=100)
        allowed, headers = limiter.check("user1")
        assert allowed is True
        assert "X-RateLimit-Limit-Minute" in headers
        assert headers["X-RateLimit-Limit-Minute"] == "5"

    def test_blocks_over_minute_limit(self):
        from packages.cloud.security.rate_limiter import InMemoryRateLimiter

        limiter = InMemoryRateLimiter(requests_per_minute=3, requests_per_hour=100)
        for _ in range(3):
            allowed, _ = limiter.check("user1")
            assert allowed is True

        allowed, headers = limiter.check("user1")
        assert allowed is False
        assert int(headers["X-RateLimit-Remaining-Minute"]) == 0

    def test_different_keys_independent(self):
        from packages.cloud.security.rate_limiter import InMemoryRateLimiter

        limiter = InMemoryRateLimiter(requests_per_minute=2, requests_per_hour=100)
        limiter.check("user1")
        limiter.check("user1")
        # user1 is at limit
        allowed, _ = limiter.check("user1")
        assert allowed is False
        # user2 is fresh
        allowed, _ = limiter.check("user2")
        assert allowed is True

    def test_headers_include_all_fields(self):
        from packages.cloud.security.rate_limiter import InMemoryRateLimiter

        limiter = InMemoryRateLimiter(requests_per_minute=10, requests_per_hour=100)
        _, headers = limiter.check("user1")
        expected_keys = {
            "X-RateLimit-Limit-Minute",
            "X-RateLimit-Remaining-Minute",
            "X-RateLimit-Limit-Hour",
            "X-RateLimit-Remaining-Hour",
            "X-RateLimit-Reset",
        }
        assert set(headers.keys()) == expected_keys

    def test_remaining_decrements(self):
        from packages.cloud.security.rate_limiter import InMemoryRateLimiter

        limiter = InMemoryRateLimiter(requests_per_minute=5, requests_per_hour=100)
        _, h1 = limiter.check("user1")
        _, h2 = limiter.check("user1")
        r1 = int(h1["X-RateLimit-Remaining-Minute"])
        r2 = int(h2["X-RateLimit-Remaining-Minute"])
        assert r2 < r1


# ---------------------------------------------------------------------------
# Sanitizer
# ---------------------------------------------------------------------------


class TestSanitizer:
    def test_sanitize_removes_script_tags(self):
        from packages.cloud.security.sanitizer import sanitize_input

        result = sanitize_input('Hello <script>alert("xss")</script> World')
        assert "<script>" not in result
        assert "alert" not in result
        assert "Hello" in result
        assert "World" in result

    def test_sanitize_removes_event_handlers(self):
        from packages.cloud.security.sanitizer import sanitize_html

        result = sanitize_html('<img src="x" onerror="alert(1)">')
        assert "onerror" not in result

    def test_sanitize_removes_javascript_urls(self):
        from packages.cloud.security.sanitizer import sanitize_input

        result = sanitize_input('javascript:alert(1)')
        assert "javascript:" not in result

    def test_sanitize_removes_null_bytes(self):
        from packages.cloud.security.sanitizer import sanitize_input

        result = sanitize_input("hello\x00world")
        assert "\x00" not in result
        assert "helloworld" in result

    def test_sanitize_preserves_normal_text(self):
        from packages.cloud.security.sanitizer import sanitize_input

        text = "This is a perfectly normal sentence."
        assert sanitize_input(text) == text

    def test_sanitize_html_preserves_safe_tags(self):
        from packages.cloud.security.sanitizer import sanitize_html

        html = "<p>Hello <strong>world</strong></p>"
        result = sanitize_html(html)
        assert "<p>" in result
        assert "<strong>" in result

    def test_validate_slug_valid(self):
        from packages.cloud.security.sanitizer import validate_slug

        assert validate_slug("my-project") is True
        assert validate_slug("project123") is True
        assert validate_slug("a") is True

    def test_validate_slug_invalid(self):
        from packages.cloud.security.sanitizer import validate_slug

        assert validate_slug("") is False
        assert validate_slug("My Project") is False
        assert validate_slug("project_name") is False
        assert validate_slug("-leading-dash") is False

    def test_sanitize_removes_expression(self):
        from packages.cloud.security.sanitizer import sanitize_html

        result = sanitize_html('background: expression(alert(1))')
        assert "expression(" not in result

    def test_sanitize_collapses_whitespace(self):
        from packages.cloud.security.sanitizer import sanitize_input

        result = sanitize_input("hello    world")
        assert result == "hello world"
