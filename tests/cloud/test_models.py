"""Tests for database model definitions (no actual database required)."""
from __future__ import annotations

import uuid

import pytest


class TestOrganizationModel:
    def test_model_has_tablename(self):
        from packages.cloud.database.models import Organization

        assert Organization.__tablename__ == "organizations"

    def test_model_columns(self):
        from packages.cloud.database.models import Organization

        cols = {c.name for c in Organization.__table__.columns}
        expected = {"id", "name", "slug", "clerk_org_id", "plan", "settings", "created_at", "updated_at"}
        assert expected.issubset(cols)

    def test_repr(self):
        from packages.cloud.database.models import Organization

        org = Organization(slug="test-org", plan="free")
        assert "test-org" in repr(org)
        assert "free" in repr(org)


class TestProjectModel:
    def test_model_has_tablename(self):
        from packages.cloud.database.models import Project

        assert Project.__tablename__ == "projects"

    def test_model_columns(self):
        from packages.cloud.database.models import Project

        cols = {c.name for c in Project.__table__.columns}
        expected = {"id", "org_id", "name", "slug", "description", "settings", "brand_dna", "created_at", "updated_at"}
        assert expected.issubset(cols)


class TestAPIKeyModel:
    def test_model_has_tablename(self):
        from packages.cloud.database.models import APIKey

        assert APIKey.__tablename__ == "api_keys"

    def test_model_columns(self):
        from packages.cloud.database.models import APIKey

        cols = {c.name for c in APIKey.__table__.columns}
        expected = {"id", "org_id", "key_hash", "prefix", "name", "scopes", "last_used_at", "expires_at", "created_at", "revoked_at"}
        assert expected.issubset(cols)


class TestUsageRecordModel:
    def test_model_has_tablename(self):
        from packages.cloud.database.models import UsageRecord

        assert UsageRecord.__tablename__ == "usage_records"

    def test_model_columns(self):
        from packages.cloud.database.models import UsageRecord

        cols = {c.name for c in UsageRecord.__table__.columns}
        expected = {"id", "org_id", "project_id", "record_type", "tokens_used", "model", "agent_slug", "created_at"}
        assert expected.issubset(cols)


class TestSubscriptionModel:
    def test_model_has_tablename(self):
        from packages.cloud.database.models import Subscription

        assert Subscription.__tablename__ == "subscriptions"

    def test_model_columns(self):
        from packages.cloud.database.models import Subscription

        cols = {c.name for c in Subscription.__table__.columns}
        expected = {"id", "org_id", "stripe_subscription_id", "stripe_customer_id", "plan", "status", "current_period_start", "current_period_end", "created_at"}
        assert expected.issubset(cols)


class TestInvoiceModel:
    def test_model_has_tablename(self):
        from packages.cloud.database.models import Invoice

        assert Invoice.__tablename__ == "invoices"

    def test_default_currency(self):
        from packages.cloud.database.models import Invoice

        inv = Invoice()
        # Check column default
        for col in Invoice.__table__.columns:
            if col.name == "currency":
                assert col.default.arg == "usd"


class TestBrandDNAModel:
    def test_model_has_tablename(self):
        from packages.cloud.database.models import BrandDNA

        assert BrandDNA.__tablename__ == "brand_dna"

    def test_model_columns(self):
        from packages.cloud.database.models import BrandDNA

        cols = {c.name for c in BrandDNA.__table__.columns}
        expected = {"id", "project_id", "voice_profile", "terminology", "content_rules", "version", "created_at"}
        assert expected.issubset(cols)


class TestConnectorConfigModel:
    def test_model_has_tablename(self):
        from packages.cloud.database.models import ConnectorConfig

        assert ConnectorConfig.__tablename__ == "connector_configs"

    def test_model_columns(self):
        from packages.cloud.database.models import ConnectorConfig

        cols = {c.name for c in ConnectorConfig.__table__.columns}
        expected = {"id", "project_id", "connector_type", "name", "credentials_encrypted", "settings", "enabled", "created_at"}
        assert expected.issubset(cols)


class TestAuditLogModel:
    def test_model_has_tablename(self):
        from packages.cloud.database.models import AuditLog

        assert AuditLog.__tablename__ == "audit_logs"

    def test_model_columns(self):
        from packages.cloud.database.models import AuditLog

        cols = {c.name for c in AuditLog.__table__.columns}
        expected = {"id", "org_id", "user_id", "action", "resource_type", "resource_id", "details", "ip_address", "created_at"}
        assert expected.issubset(cols)


class TestAllModels:
    def test_all_models_share_base(self):
        from packages.cloud.database.models import (
            AuditLog,
            Base,
            BrandDNA,
            ConnectorConfig,
            Invoice,
            Organization,
            Project,
            Subscription,
            UsageRecord,
            APIKey,
        )

        for model in [Organization, Project, APIKey, UsageRecord, Subscription, Invoice, BrandDNA, ConnectorConfig, AuditLog]:
            assert issubclass(model, Base)

    def test_model_count(self):
        from packages.cloud.database.models import Base

        # We should have 9 models
        assert len(Base.metadata.tables) >= 9
