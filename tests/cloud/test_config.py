"""Tests for cloud configuration."""
from __future__ import annotations

from unittest.mock import patch

import pytest


class TestCloudConfig:
    def test_default_values(self):
        from packages.cloud.config import CloudConfig

        config = CloudConfig()
        assert config.database_url == ""
        assert config.redis_url == ""
        assert config.clerk_secret_key == ""
        assert config.stripe_api_key == ""
        assert config.cors_origins == []

    def test_config_is_frozen(self):
        from packages.cloud.config import CloudConfig

        config = CloudConfig()
        with pytest.raises(AttributeError):
            config.database_url = "new-url"  # type: ignore[misc]

    def test_load_from_env(self):
        from packages.cloud.config import _load_config

        env = {
            "DATABASE_URL": "postgresql://test:test@db/test",
            "REDIS_URL": "redis://redis:6379/1",
            "CLERK_SECRET_KEY": "sk_test_123",
            "CLERK_PUBLISHABLE_KEY": "pk_test_123",
            "STRIPE_API_KEY": "sk_test_stripe",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
            "ENCRYPTION_KEY": "my-secret-key",
            "CORS_ORIGINS": "http://localhost:3000,https://app.example.com",
        }
        with patch.dict("os.environ", env, clear=False):
            config = _load_config()

        assert config.database_url == "postgresql://test:test@db/test"
        assert config.redis_url == "redis://redis:6379/1"
        assert config.clerk_secret_key == "sk_test_123"
        assert config.stripe_api_key == "sk_test_stripe"
        assert config.encryption_key == "my-secret-key"
        assert "http://localhost:3000" in config.cors_origins
        assert "https://app.example.com" in config.cors_origins

    def test_default_cors(self):
        from packages.cloud.config import _load_config

        with patch.dict("os.environ", {}, clear=False):
            config = _load_config()

        assert "http://localhost:3000" in config.cors_origins

    def test_default_database_url(self):
        from packages.cloud.config import _load_config

        env_without_db = {k: v for k, v in __import__("os").environ.items() if k != "DATABASE_URL"}
        with patch.dict("os.environ", env_without_db, clear=True):
            config = _load_config()

        assert "postgresql://" in config.database_url
        assert "cdagency" in config.database_url
