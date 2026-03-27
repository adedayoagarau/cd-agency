"""Content governance — approval gates, audit trails, and change tracking.

Provides enterprise-grade content governance:
- AuditLog: Immutable, append-only log of all content changes
- ApprovalGate: Configurable approval requirements before content ships
- ChangeRecord: Tracks terminology, brand voice, and content changes
- GovernancePolicy: Configurable rules for content governance
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any


_GOVERNANCE_DIR = ".cd-agency"
_AUDIT_FILE = "audit_log.json"
_CHANGES_FILE = "change_records.json"
_POLICY_FILE = "governance_policy.json"
_MAX_AUDIT_ENTRIES = 5000
_MAX_CHANGE_RECORDS = 1000


class ChangeType(str, Enum):
    TERMINOLOGY = "terminology"
    BRAND_VOICE = "brand_voice"
    CONTENT = "content"
    STYLE_RULE = "style_rule"
    APPROVAL = "approval"
    REJECTION = "rejection"
    MEMORY = "memory"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


@dataclass
class AuditEntry:
    """Single entry in the audit log — immutable once created."""

    id: str = ""
    timestamp: float = 0.0
    action: str = ""
    change_type: str = ""
    actor: str = ""  # agent name or "user"
    description: str = ""
    before_value: str = ""
    after_value: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class ChangeRecord:
    """Tracks a specific change to content, terminology, or brand voice."""

    id: str = ""
    timestamp: float = 0.0
    change_type: str = ""
    key: str = ""
    before_value: str = ""
    after_value: str = ""
    reason: str = ""
    source_agent: str = ""
    approval_status: str = "pending"
    approved_by: str = ""
    approval_timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class ApprovalGate:
    """Defines approval requirements for a type of change."""

    change_type: str = ""
    requires_approval: bool = True
    auto_approve_agents: list[str] = field(default_factory=list)
    min_quality_score: float = 0.0  # Auto-approve if score exceeds this
    description: str = ""


@dataclass
class GovernancePolicy:
    """Configurable governance rules."""

    approval_gates: list[ApprovalGate] = field(default_factory=list)
    require_audit: bool = True
    max_pending_changes: int = 50
    auto_approve_threshold: float = 85.0  # Composite score for auto-approval

    @classmethod
    def default(cls) -> GovernancePolicy:
        """Create default governance policy."""
        return cls(
            approval_gates=[
                ApprovalGate(
                    change_type=ChangeType.TERMINOLOGY,
                    requires_approval=True,
                    description="Terminology changes require explicit approval.",
                ),
                ApprovalGate(
                    change_type=ChangeType.BRAND_VOICE,
                    requires_approval=True,
                    description="Brand voice changes require explicit approval.",
                ),
                ApprovalGate(
                    change_type=ChangeType.CONTENT,
                    requires_approval=False,
                    auto_approve_agents=["content-designer-generalist"],
                    min_quality_score=80.0,
                    description="Content changes auto-approved above quality threshold.",
                ),
                ApprovalGate(
                    change_type=ChangeType.STYLE_RULE,
                    requires_approval=True,
                    description="Style rule changes require explicit approval.",
                ),
            ],
        )


class AuditLog:
    """Append-only audit log for content governance."""

    def __init__(self, project_dir: Path | str | None = None) -> None:
        self.project_dir = Path(project_dir) if project_dir else Path(".")
        self._entries: list[AuditEntry] | None = None

    @property
    def storage_path(self) -> Path:
        return self.project_dir / _GOVERNANCE_DIR / _AUDIT_FILE

    @property
    def entries(self) -> list[AuditEntry]:
        if self._entries is None:
            self._entries = self._load()
        return self._entries

    def _load(self) -> list[AuditEntry]:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return [AuditEntry(**e) for e in data]
            except (json.JSONDecodeError, TypeError, OSError):
                pass
        return []

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        trimmed = self.entries[-_MAX_AUDIT_ENTRIES:]
        self.storage_path.write_text(
            json.dumps([asdict(e) for e in trimmed], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def log(
        self,
        action: str,
        change_type: str,
        actor: str = "system",
        description: str = "",
        before_value: str = "",
        after_value: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """Add an entry to the audit log."""
        entry = AuditEntry(
            action=action,
            change_type=change_type,
            actor=actor,
            description=description,
            before_value=before_value,
            after_value=after_value,
            metadata=metadata or {},
        )
        self.entries.append(entry)
        self._save()
        return entry

    def get_recent(self, n: int = 20) -> list[AuditEntry]:
        """Get the most recent audit entries."""
        return self.entries[-n:]

    def get_by_type(self, change_type: str) -> list[AuditEntry]:
        """Get entries filtered by change type."""
        return [e for e in self.entries if e.change_type == change_type]

    def get_by_actor(self, actor: str) -> list[AuditEntry]:
        """Get entries by actor (agent name or 'user')."""
        return [e for e in self.entries if e.actor == actor]

    def search(self, query: str) -> list[AuditEntry]:
        """Search audit log entries."""
        q = query.lower()
        return [
            e for e in self.entries
            if q in e.description.lower()
            or q in e.action.lower()
            or q in e.before_value.lower()
            or q in e.after_value.lower()
        ]

    def count(self) -> int:
        return len(self.entries)

    def clear(self) -> int:
        """Clear all entries. Returns count removed."""
        n = len(self.entries)
        self._entries = []
        self._save()
        return n


class ChangeTracker:
    """Tracks content, terminology, and brand voice changes with approval workflow."""

    def __init__(self, project_dir: Path | str | None = None) -> None:
        self.project_dir = Path(project_dir) if project_dir else Path(".")
        self._records: list[ChangeRecord] | None = None
        self._policy: GovernancePolicy | None = None
        self.audit_log = AuditLog(project_dir=self.project_dir)

    @property
    def storage_path(self) -> Path:
        return self.project_dir / _GOVERNANCE_DIR / _CHANGES_FILE

    @property
    def records(self) -> list[ChangeRecord]:
        if self._records is None:
            self._records = self._load()
        return self._records

    @property
    def policy(self) -> GovernancePolicy:
        if self._policy is None:
            self._policy = self._load_policy()
        return self._policy

    def _load(self) -> list[ChangeRecord]:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return [ChangeRecord(**r) for r in data]
            except (json.JSONDecodeError, TypeError, OSError):
                pass
        return []

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        trimmed = self.records[-_MAX_CHANGE_RECORDS:]
        self.storage_path.write_text(
            json.dumps([asdict(r) for r in trimmed], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_policy(self) -> GovernancePolicy:
        policy_path = self.project_dir / _GOVERNANCE_DIR / _POLICY_FILE
        if policy_path.exists():
            try:
                data = json.loads(policy_path.read_text(encoding="utf-8"))
                gates = [ApprovalGate(**g) for g in data.get("approval_gates", [])]
                return GovernancePolicy(
                    approval_gates=gates,
                    require_audit=data.get("require_audit", True),
                    max_pending_changes=data.get("max_pending_changes", 50),
                    auto_approve_threshold=data.get("auto_approve_threshold", 85.0),
                )
            except (json.JSONDecodeError, TypeError, OSError):
                pass
        return GovernancePolicy.default()

    def save_policy(self) -> None:
        """Persist governance policy."""
        policy_path = self.project_dir / _GOVERNANCE_DIR / _POLICY_FILE
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "approval_gates": [asdict(g) for g in self.policy.approval_gates],
            "require_audit": self.policy.require_audit,
            "max_pending_changes": self.policy.max_pending_changes,
            "auto_approve_threshold": self.policy.auto_approve_threshold,
        }
        policy_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def propose_change(
        self,
        change_type: str,
        key: str,
        before_value: str,
        after_value: str,
        reason: str = "",
        source_agent: str = "",
        quality_score: float = 0.0,
    ) -> ChangeRecord:
        """Propose a content change, applying approval policy."""
        record = ChangeRecord(
            change_type=change_type,
            key=key,
            before_value=before_value,
            after_value=after_value,
            reason=reason,
            source_agent=source_agent,
        )

        # Check approval gate
        gate = self._find_gate(change_type)
        if gate is None or not gate.requires_approval:
            record.approval_status = ApprovalStatus.AUTO_APPROVED
            record.approved_by = "policy:no_approval_required"
            record.approval_timestamp = time.time()
        elif source_agent in (gate.auto_approve_agents or []):
            record.approval_status = ApprovalStatus.AUTO_APPROVED
            record.approved_by = f"policy:trusted_agent:{source_agent}"
            record.approval_timestamp = time.time()
        elif gate.min_quality_score and quality_score >= gate.min_quality_score:
            record.approval_status = ApprovalStatus.AUTO_APPROVED
            record.approved_by = f"policy:quality_score:{quality_score:.0f}"
            record.approval_timestamp = time.time()

        self.records.append(record)
        self._save()

        # Audit log
        if self.policy.require_audit:
            self.audit_log.log(
                action="change_proposed",
                change_type=change_type,
                actor=source_agent or "user",
                description=f"Change proposed for '{key}': {reason}",
                before_value=before_value,
                after_value=after_value,
                metadata={
                    "record_id": record.id,
                    "approval_status": record.approval_status,
                    "quality_score": quality_score,
                },
            )

        return record

    def approve(self, record_id: str, approved_by: str = "user") -> bool:
        """Approve a pending change."""
        for record in self.records:
            if record.id == record_id and record.approval_status == ApprovalStatus.PENDING:
                record.approval_status = ApprovalStatus.APPROVED
                record.approved_by = approved_by
                record.approval_timestamp = time.time()
                self._save()

                self.audit_log.log(
                    action="change_approved",
                    change_type=record.change_type,
                    actor=approved_by,
                    description=f"Approved change for '{record.key}'",
                    metadata={"record_id": record_id},
                )
                return True
        return False

    def reject(self, record_id: str, rejected_by: str = "user", reason: str = "") -> bool:
        """Reject a pending change."""
        for record in self.records:
            if record.id == record_id and record.approval_status == ApprovalStatus.PENDING:
                record.approval_status = ApprovalStatus.REJECTED
                record.approved_by = rejected_by
                record.approval_timestamp = time.time()
                record.metadata["rejection_reason"] = reason
                self._save()

                self.audit_log.log(
                    action="change_rejected",
                    change_type=record.change_type,
                    actor=rejected_by,
                    description=f"Rejected change for '{record.key}': {reason}",
                    metadata={"record_id": record_id},
                )
                return True
        return False

    def get_pending(self) -> list[ChangeRecord]:
        """Get all pending changes."""
        return [r for r in self.records if r.approval_status == ApprovalStatus.PENDING]

    def get_approved(self) -> list[ChangeRecord]:
        """Get all approved changes."""
        return [
            r for r in self.records
            if r.approval_status in (ApprovalStatus.APPROVED, ApprovalStatus.AUTO_APPROVED)
        ]

    def get_by_type(self, change_type: str) -> list[ChangeRecord]:
        """Get changes by type."""
        return [r for r in self.records if r.change_type == change_type]

    def _find_gate(self, change_type: str) -> ApprovalGate | None:
        """Find the approval gate for a change type."""
        for gate in self.policy.approval_gates:
            if gate.change_type == change_type:
                return gate
        return None

    def pending_count(self) -> int:
        return len(self.get_pending())

    def total_count(self) -> int:
        return len(self.records)
