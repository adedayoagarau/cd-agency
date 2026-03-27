"""SQLAlchemy 2.0 models for the CD Agency multi-tenant SaaS platform."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Declarative base for all CD Agency models."""
    pass


class Organization(Base):
    """A tenant organization — the top-level isolation boundary."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    clerk_org_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    projects: Mapped[list[Project]] = relationship(
        "Project", back_populates="organization", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list[APIKey]] = relationship(
        "APIKey", back_populates="organization", cascade="all, delete-orphan"
    )
    usage_records: Mapped[list[UsageRecord]] = relationship(
        "UsageRecord", back_populates="organization", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list[Subscription]] = relationship(
        "Subscription", back_populates="organization", cascade="all, delete-orphan"
    )
    invoices: Mapped[list[Invoice]] = relationship(
        "Invoice", back_populates="organization", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        "AuditLog", back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization {self.slug!r} plan={self.plan!r}>"


class Project(Base):
    """A project within an organization — groups content, brand DNA, and connectors."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    brand_dna: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="projects"
    )
    usage_records: Mapped[list[UsageRecord]] = relationship(
        "UsageRecord", back_populates="project", cascade="all, delete-orphan"
    )
    brand_dna_versions: Mapped[list[BrandDNA]] = relationship(
        "BrandDNA", back_populates="project", cascade="all, delete-orphan"
    )
    connector_configs: Mapped[list[ConnectorConfig]] = relationship(
        "ConnectorConfig", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Slug is unique per organization
        {"comment": "org_id + slug should be unique; enforce via unique index in migration"},
    )

    def __repr__(self) -> str:
        return f"<Project {self.slug!r} org={self.org_id!r}>"


class APIKey(Base):
    """An API key bound to an organization. The raw key is never stored — only its SHA-256 hash."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    prefix: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="api_keys"
    )

    @property
    def is_active(self) -> bool:
        """Return True if the key has not been revoked and has not expired."""
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and self.expires_at < datetime.utcnow():
            return False
        return True

    def __repr__(self) -> str:
        return f"<APIKey {self.prefix!r}*** name={self.name!r}>"


class UsageRecord(Base):
    """A single usage event — agent run, score, or API call."""

    __tablename__ = "usage_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    record_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # agent_run | score | api_call
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    agent_slug: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    # Relationships
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="usage_records"
    )
    project: Mapped[Optional[Project]] = relationship(
        "Project", back_populates="usage_records"
    )

    def __repr__(self) -> str:
        return f"<UsageRecord {self.record_type!r} tokens={self.tokens_used}>"


class Subscription(Base):
    """Stripe subscription state mirrored locally for fast plan checks."""

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    plan: Mapped[str] = mapped_column(
        String(50), nullable=False, default="free"
    )  # free | starter | pro | enterprise
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )  # active | past_due | canceled | trialing
    current_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="subscriptions"
    )

    def __repr__(self) -> str:
        return f"<Subscription plan={self.plan!r} status={self.status!r}>"


class Invoice(Base):
    """Stripe invoice record mirrored locally."""

    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="usd")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="draft"
    )  # draft | open | paid | void | uncollectible
    period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="invoices"
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.amount_cents}c {self.currency} status={self.status!r}>"


class BrandDNA(Base):
    """Versioned brand DNA snapshot for a project — voice, terminology, content rules."""

    __tablename__ = "brand_dna"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    voice_profile: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    terminology: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    content_rules: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    project: Mapped[Project] = relationship(
        "Project", back_populates="brand_dna_versions"
    )

    def __repr__(self) -> str:
        return f"<BrandDNA project={self.project_id!r} v{self.version}>"


class ConnectorConfig(Base):
    """External connector configuration for a project (Figma, GitHub, CMS, etc.)."""

    __tablename__ = "connector_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    connector_type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    credentials_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    project: Mapped[Project] = relationship(
        "Project", back_populates="connector_configs"
    )

    def __repr__(self) -> str:
        return f"<ConnectorConfig {self.connector_type!r} name={self.name!r}>"


class AuditLog(Base):
    """Immutable audit trail for security-sensitive actions."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    # Relationships
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="audit_logs"
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action!r} user={self.user_id!r}>"
