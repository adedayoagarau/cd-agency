"""Tests for content governance — audit log, change tracking, approval workflow."""

from __future__ import annotations

import pytest

from runtime.governance import (
    ApprovalGate,
    ApprovalStatus,
    AuditEntry,
    AuditLog,
    ChangeRecord,
    ChangeTracker,
    ChangeType,
    GovernancePolicy,
)


# ---------------------------------------------------------------------------
# AuditEntry
# ---------------------------------------------------------------------------

class TestAuditEntry:
    def test_defaults(self):
        entry = AuditEntry(action="create", change_type="content")
        assert entry.id != ""
        assert entry.timestamp > 0
        assert entry.action == "create"

    def test_explicit_values(self):
        entry = AuditEntry(
            id="test-id",
            action="update",
            change_type="terminology",
            actor="user",
            description="Changed login to sign in",
            before_value="log in",
            after_value="sign in",
        )
        assert entry.id == "test-id"
        assert entry.actor == "user"


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------

class TestAuditLog:
    def test_empty_log(self, tmp_path):
        log = AuditLog(project_dir=tmp_path)
        assert log.count() == 0

    def test_log_entry(self, tmp_path):
        log = AuditLog(project_dir=tmp_path)
        entry = log.log(
            action="create",
            change_type="content",
            actor="error-message-architect",
            description="Created error message",
        )
        assert entry.id != ""
        assert log.count() == 1

    def test_persistence(self, tmp_path):
        log1 = AuditLog(project_dir=tmp_path)
        log1.log(action="test", change_type="content", actor="user")

        log2 = AuditLog(project_dir=tmp_path)
        assert log2.count() == 1

    def test_get_recent(self, tmp_path):
        log = AuditLog(project_dir=tmp_path)
        for i in range(5):
            log.log(action=f"action-{i}", change_type="content")

        recent = log.get_recent(3)
        assert len(recent) == 3

    def test_get_by_type(self, tmp_path):
        log = AuditLog(project_dir=tmp_path)
        log.log(action="a", change_type="content")
        log.log(action="b", change_type="terminology")
        log.log(action="c", change_type="content")

        content_entries = log.get_by_type("content")
        assert len(content_entries) == 2

    def test_get_by_actor(self, tmp_path):
        log = AuditLog(project_dir=tmp_path)
        log.log(action="a", change_type="content", actor="user")
        log.log(action="b", change_type="content", actor="agent")
        log.log(action="c", change_type="content", actor="user")

        user_entries = log.get_by_actor("user")
        assert len(user_entries) == 2

    def test_search(self, tmp_path):
        log = AuditLog(project_dir=tmp_path)
        log.log(action="a", change_type="content", description="Changed button text")
        log.log(action="b", change_type="content", description="Updated modal")

        results = log.search("button")
        assert len(results) == 1

    def test_clear(self, tmp_path):
        log = AuditLog(project_dir=tmp_path)
        log.log(action="a", change_type="content")
        log.log(action="b", change_type="content")

        removed = log.clear()
        assert removed == 2
        assert log.count() == 0


# ---------------------------------------------------------------------------
# ChangeRecord
# ---------------------------------------------------------------------------

class TestChangeRecord:
    def test_defaults(self):
        record = ChangeRecord(change_type="content", key="button-text")
        assert record.id != ""
        assert record.timestamp > 0
        assert record.approval_status == "pending"

    def test_explicit_values(self):
        record = ChangeRecord(
            change_type="terminology",
            key="login",
            before_value="log in",
            after_value="sign in",
            reason="Brand guidelines",
            source_agent="brand-voice-archaeologist",
        )
        assert record.before_value == "log in"
        assert record.after_value == "sign in"


# ---------------------------------------------------------------------------
# GovernancePolicy
# ---------------------------------------------------------------------------

class TestGovernancePolicy:
    def test_default_policy(self):
        policy = GovernancePolicy.default()
        assert len(policy.approval_gates) == 4
        assert policy.require_audit is True
        assert policy.auto_approve_threshold == 85.0

    def test_terminology_requires_approval(self):
        policy = GovernancePolicy.default()
        term_gate = None
        for gate in policy.approval_gates:
            if gate.change_type == ChangeType.TERMINOLOGY:
                term_gate = gate
                break
        assert term_gate is not None
        assert term_gate.requires_approval is True


# ---------------------------------------------------------------------------
# ChangeTracker
# ---------------------------------------------------------------------------

class TestChangeTracker:
    def test_empty_tracker(self, tmp_path):
        tracker = ChangeTracker(project_dir=tmp_path)
        assert tracker.pending_count() == 0
        assert tracker.total_count() == 0

    def test_propose_terminology_change(self, tmp_path):
        tracker = ChangeTracker(project_dir=tmp_path)
        record = tracker.propose_change(
            change_type=ChangeType.TERMINOLOGY,
            key="login",
            before_value="log in",
            after_value="sign in",
            reason="Brand guide says sign in",
            source_agent="brand-voice-archaeologist",
        )

        assert record.approval_status == ApprovalStatus.PENDING
        assert tracker.pending_count() == 1

    def test_propose_content_change_auto_approved(self, tmp_path):
        tracker = ChangeTracker(project_dir=tmp_path)
        record = tracker.propose_change(
            change_type=ChangeType.CONTENT,
            key="error-msg",
            before_value="Error occurred",
            after_value="Something went wrong. Please try again.",
            source_agent="content-designer-generalist",
        )

        # Content changes from trusted agents are auto-approved
        assert record.approval_status == ApprovalStatus.AUTO_APPROVED

    def test_propose_content_change_by_quality(self, tmp_path):
        tracker = ChangeTracker(project_dir=tmp_path)
        record = tracker.propose_change(
            change_type=ChangeType.CONTENT,
            key="button-text",
            before_value="Submit",
            after_value="Save changes",
            source_agent="unknown-agent",
            quality_score=90.0,
        )

        # High quality score auto-approves
        assert record.approval_status == ApprovalStatus.AUTO_APPROVED

    def test_approve_change(self, tmp_path):
        tracker = ChangeTracker(project_dir=tmp_path)
        record = tracker.propose_change(
            change_type=ChangeType.TERMINOLOGY,
            key="login",
            before_value="log in",
            after_value="sign in",
        )

        assert tracker.approve(record.id, "admin") is True
        assert tracker.pending_count() == 0
        assert len(tracker.get_approved()) == 1

    def test_reject_change(self, tmp_path):
        tracker = ChangeTracker(project_dir=tmp_path)
        record = tracker.propose_change(
            change_type=ChangeType.TERMINOLOGY,
            key="login",
            before_value="log in",
            after_value="sign in",
        )

        assert tracker.reject(record.id, "admin", "Not aligned with brand") is True
        assert tracker.pending_count() == 0

    def test_approve_nonexistent(self, tmp_path):
        tracker = ChangeTracker(project_dir=tmp_path)
        assert tracker.approve("nonexistent") is False

    def test_reject_nonexistent(self, tmp_path):
        tracker = ChangeTracker(project_dir=tmp_path)
        assert tracker.reject("nonexistent") is False

    def test_persistence(self, tmp_path):
        tracker1 = ChangeTracker(project_dir=tmp_path)
        tracker1.propose_change(
            change_type=ChangeType.CONTENT,
            key="test",
            before_value="a",
            after_value="b",
        )

        tracker2 = ChangeTracker(project_dir=tmp_path)
        assert tracker2.total_count() == 1

    def test_get_by_type(self, tmp_path):
        tracker = ChangeTracker(project_dir=tmp_path)
        tracker.propose_change(change_type=ChangeType.CONTENT, key="a", before_value="", after_value="x")
        tracker.propose_change(change_type=ChangeType.TERMINOLOGY, key="b", before_value="", after_value="y")
        tracker.propose_change(change_type=ChangeType.CONTENT, key="c", before_value="", after_value="z")

        content_changes = tracker.get_by_type(ChangeType.CONTENT)
        assert len(content_changes) == 2

    def test_audit_log_created(self, tmp_path):
        tracker = ChangeTracker(project_dir=tmp_path)
        tracker.propose_change(
            change_type=ChangeType.TERMINOLOGY,
            key="test",
            before_value="a",
            after_value="b",
        )

        assert tracker.audit_log.count() == 1

    def test_approve_creates_audit_entry(self, tmp_path):
        tracker = ChangeTracker(project_dir=tmp_path)
        record = tracker.propose_change(
            change_type=ChangeType.TERMINOLOGY,
            key="test",
            before_value="a",
            after_value="b",
        )
        tracker.approve(record.id, "admin")

        # Should have 2 audit entries: propose + approve
        assert tracker.audit_log.count() == 2

    def test_save_and_load_policy(self, tmp_path):
        tracker = ChangeTracker(project_dir=tmp_path)
        tracker._policy = GovernancePolicy.default()
        tracker.save_policy()

        tracker2 = ChangeTracker(project_dir=tmp_path)
        assert len(tracker2.policy.approval_gates) > 0
