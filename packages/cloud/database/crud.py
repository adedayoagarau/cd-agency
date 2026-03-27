"""CRUD operations for CD Agency Cloud multi-tenant models."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from .models import (
    APIKey,
    AuditLog,
    Organization,
    Project,
    Subscription,
    UsageRecord,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

API_KEY_PREFIX_LENGTH = 8
API_KEY_SECRET_LENGTH = 32


def _hash_key(raw_key: str) -> str:
    """Return the SHA-256 hex digest of *raw_key*."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _generate_api_key() -> tuple[str, str, str]:
    """Generate an API key, returning ``(full_key, prefix, key_hash)``."""
    prefix = secrets.token_hex(API_KEY_PREFIX_LENGTH // 2)  # 8 hex chars
    secret = secrets.token_hex(API_KEY_SECRET_LENGTH // 2)  # 32 hex chars
    full_key = f"cda_{prefix}_{secret}"
    key_hash = _hash_key(full_key)
    return full_key, prefix, key_hash


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# OrganizationCRUD
# ---------------------------------------------------------------------------


class OrganizationCRUD:
    """CRUD helpers for :class:`Organization`."""

    @staticmethod
    def create(
        session: Session,
        *,
        name: str,
        slug: str,
        clerk_org_id: str | None = None,
        plan: str = "free",
        settings: dict | None = None,
    ) -> Organization:
        org = Organization(
            name=name,
            slug=slug,
            clerk_org_id=clerk_org_id,
            plan=plan,
            settings=settings or {},
        )
        session.add(org)
        session.flush()
        return org

    @staticmethod
    def get_by_id(session: Session, org_id: uuid.UUID) -> Organization | None:
        return session.get(Organization, org_id)

    @staticmethod
    def get_by_slug(session: Session, slug: str) -> Organization | None:
        stmt = select(Organization).where(Organization.slug == slug)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_clerk_id(session: Session, clerk_org_id: str) -> Organization | None:
        stmt = select(Organization).where(Organization.clerk_org_id == clerk_org_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def update(
        session: Session,
        org_id: uuid.UUID,
        **kwargs: object,
    ) -> Organization | None:
        org = session.get(Organization, org_id)
        if org is None:
            return None
        for key, value in kwargs.items():
            if hasattr(org, key):
                setattr(org, key, value)
        session.flush()
        return org

    @staticmethod
    def list_all(
        session: Session,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Organization]:
        stmt = (
            select(Organization)
            .order_by(Organization.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.execute(stmt).scalars().all())


# ---------------------------------------------------------------------------
# ProjectCRUD
# ---------------------------------------------------------------------------


class ProjectCRUD:
    """CRUD helpers for :class:`Project`."""

    @staticmethod
    def create(
        session: Session,
        *,
        org_id: uuid.UUID,
        name: str,
        slug: str,
        description: str | None = None,
        settings: dict | None = None,
        brand_dna: dict | None = None,
    ) -> Project:
        project = Project(
            org_id=org_id,
            name=name,
            slug=slug,
            description=description,
            settings=settings or {},
            brand_dna=brand_dna or {},
        )
        session.add(project)
        session.flush()
        return project

    @staticmethod
    def get_by_id(session: Session, project_id: uuid.UUID) -> Project | None:
        return session.get(Project, project_id)

    @staticmethod
    def get_by_slug(session: Session, org_id: uuid.UUID, slug: str) -> Project | None:
        stmt = select(Project).where(
            and_(Project.org_id == org_id, Project.slug == slug)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_by_org(
        session: Session,
        org_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Project]:
        stmt = (
            select(Project)
            .where(Project.org_id == org_id)
            .order_by(Project.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def update(
        session: Session,
        project_id: uuid.UUID,
        **kwargs: object,
    ) -> Project | None:
        project = session.get(Project, project_id)
        if project is None:
            return None
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        session.flush()
        return project

    @staticmethod
    def delete(session: Session, project_id: uuid.UUID) -> bool:
        project = session.get(Project, project_id)
        if project is None:
            return False
        session.delete(project)
        session.flush()
        return True


# ---------------------------------------------------------------------------
# APIKeyCRUD
# ---------------------------------------------------------------------------


class APIKeyCRUD:
    """CRUD helpers for :class:`APIKey`.

    ``create`` returns a tuple of ``(APIKey, raw_key)`` — the raw key is
    shown to the user exactly once and is never stored.
    """

    @staticmethod
    def create(
        session: Session,
        *,
        org_id: uuid.UUID,
        name: str,
        scopes: list[str] | None = None,
        expires_at: datetime | None = None,
    ) -> tuple[APIKey, str]:
        """Create a new API key. Returns ``(api_key_row, raw_key)``."""
        full_key, prefix, key_hash = _generate_api_key()
        api_key = APIKey(
            org_id=org_id,
            key_hash=key_hash,
            prefix=prefix,
            name=name,
            scopes=scopes or [],
            expires_at=expires_at,
        )
        session.add(api_key)
        session.flush()
        return api_key, full_key

    @staticmethod
    def verify(session: Session, raw_key: str) -> APIKey | None:
        """Look up an API key by its raw value and return the row if active."""
        key_hash = _hash_key(raw_key)
        stmt = select(APIKey).where(APIKey.key_hash == key_hash)
        api_key = session.execute(stmt).scalar_one_or_none()
        if api_key is None or not api_key.is_active:
            return None
        # Touch last_used_at
        api_key.last_used_at = _utcnow()
        session.flush()
        return api_key

    @staticmethod
    def revoke(session: Session, api_key_id: uuid.UUID) -> APIKey | None:
        api_key = session.get(APIKey, api_key_id)
        if api_key is None:
            return None
        api_key.revoked_at = _utcnow()
        session.flush()
        return api_key

    @staticmethod
    def list_by_org(
        session: Session,
        org_id: uuid.UUID,
        *,
        include_revoked: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[APIKey]:
        stmt = select(APIKey).where(APIKey.org_id == org_id)
        if not include_revoked:
            stmt = stmt.where(APIKey.revoked_at.is_(None))
        stmt = stmt.order_by(APIKey.created_at.desc()).offset(offset).limit(limit)
        return list(session.execute(stmt).scalars().all())


# ---------------------------------------------------------------------------
# UsageRecordCRUD
# ---------------------------------------------------------------------------


class UsageRecordCRUD:
    """CRUD helpers for :class:`UsageRecord`."""

    @staticmethod
    def create(
        session: Session,
        *,
        org_id: uuid.UUID,
        record_type: str,
        tokens_used: int = 0,
        project_id: uuid.UUID | None = None,
        model: str | None = None,
        agent_slug: str | None = None,
    ) -> UsageRecord:
        record = UsageRecord(
            org_id=org_id,
            project_id=project_id,
            record_type=record_type,
            tokens_used=tokens_used,
            model=model,
            agent_slug=agent_slug,
        )
        session.add(record)
        session.flush()
        return record

    @staticmethod
    def get_by_org(
        session: Session,
        org_id: uuid.UUID,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        record_type: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[UsageRecord]:
        stmt = select(UsageRecord).where(UsageRecord.org_id == org_id)
        if start is not None:
            stmt = stmt.where(UsageRecord.created_at >= start)
        if end is not None:
            stmt = stmt.where(UsageRecord.created_at <= end)
        if record_type is not None:
            stmt = stmt.where(UsageRecord.record_type == record_type)
        stmt = stmt.order_by(UsageRecord.created_at.desc()).offset(offset).limit(limit)
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_summary(
        session: Session,
        org_id: uuid.UUID,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict:
        """Return an aggregate summary of usage for the given period.

        Returns a dict with ``total_tokens``, ``total_records``, and a
        breakdown ``by_type`` mapping record_type to token count.
        """
        base = select(
            UsageRecord.record_type,
            func.sum(UsageRecord.tokens_used).label("tokens"),
            func.count(UsageRecord.id).label("count"),
        ).where(UsageRecord.org_id == org_id)

        if start is not None:
            base = base.where(UsageRecord.created_at >= start)
        if end is not None:
            base = base.where(UsageRecord.created_at <= end)

        base = base.group_by(UsageRecord.record_type)
        rows = session.execute(base).all()

        by_type: dict[str, dict[str, int]] = {}
        total_tokens = 0
        total_records = 0
        for record_type, tokens, count in rows:
            by_type[record_type] = {"tokens": int(tokens or 0), "count": int(count)}
            total_tokens += int(tokens or 0)
            total_records += int(count)

        return {
            "total_tokens": total_tokens,
            "total_records": total_records,
            "by_type": by_type,
        }


# ---------------------------------------------------------------------------
# SubscriptionCRUD
# ---------------------------------------------------------------------------


class SubscriptionCRUD:
    """CRUD helpers for :class:`Subscription`."""

    @staticmethod
    def create(
        session: Session,
        *,
        org_id: uuid.UUID,
        stripe_subscription_id: str | None = None,
        stripe_customer_id: str | None = None,
        plan: str = "free",
        status: str = "active",
        current_period_start: datetime | None = None,
        current_period_end: datetime | None = None,
    ) -> Subscription:
        sub = Subscription(
            org_id=org_id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            plan=plan,
            status=status,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
        )
        session.add(sub)
        session.flush()
        return sub

    @staticmethod
    def get_by_org(session: Session, org_id: uuid.UUID) -> Subscription | None:
        """Return the most recent subscription for an org."""
        stmt = (
            select(Subscription)
            .where(Subscription.org_id == org_id)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def update_from_stripe(
        session: Session,
        stripe_subscription_id: str,
        *,
        plan: str | None = None,
        status: str | None = None,
        current_period_start: datetime | None = None,
        current_period_end: datetime | None = None,
    ) -> Subscription | None:
        """Update a subscription from a Stripe webhook payload."""
        stmt = select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription_id
        )
        sub = session.execute(stmt).scalar_one_or_none()
        if sub is None:
            return None
        if plan is not None:
            sub.plan = plan
        if status is not None:
            sub.status = status
        if current_period_start is not None:
            sub.current_period_start = current_period_start
        if current_period_end is not None:
            sub.current_period_end = current_period_end
        session.flush()
        return sub


# ---------------------------------------------------------------------------
# AuditLogCRUD
# ---------------------------------------------------------------------------


class AuditLogCRUD:
    """CRUD helpers for :class:`AuditLog`."""

    @staticmethod
    def create(
        session: Session,
        *,
        org_id: uuid.UUID,
        action: str,
        user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            org_id=org_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        session.add(entry)
        session.flush()
        return entry

    @staticmethod
    def list_by_org(
        session: Session,
        org_id: uuid.UUID,
        *,
        user_id: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.org_id == org_id)
        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        if resource_type is not None:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if start is not None:
            stmt = stmt.where(AuditLog.created_at >= start)
        if end is not None:
            stmt = stmt.where(AuditLog.created_at <= end)
        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        return list(session.execute(stmt).scalars().all())
