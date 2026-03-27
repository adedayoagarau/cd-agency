"""V2 Scoring endpoints — readability, linter, a11y, and combined."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from tools.a11y_checker import A11yChecker
from tools.linter import ContentLinter
from tools.scoring import ReadabilityScorer

router = APIRouter(prefix="/api/v2/score", tags=["scoring-v2"])

# Re-use scorer instances across requests (they are stateless).
_readability_scorer = ReadabilityScorer()
_content_linter = ContentLinter()
_a11y_checker = A11yChecker()


# ── Request / Response Models ────────────────────────────────────────────────


class ScoreRequestV2(BaseModel):
    text: str = Field(..., min_length=1, description="Text content to score")


class ReadabilityResponseV2(BaseModel):
    word_count: int
    character_count: int
    sentence_count: int
    syllable_count: int
    avg_sentence_length: float
    max_sentence_length: int
    min_sentence_length: int
    avg_word_length: float
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    complexity_index: float
    reading_time_seconds: float
    grade_label: str
    ease_label: str


class LintIssueV2(BaseModel):
    rule: str
    passed: bool
    severity: str
    message: str
    suggestion: str = ""
    matches: list[str] = []


class LintResponseV2(BaseModel):
    issues: list[LintIssueV2]
    passed_count: int
    failed_count: int
    total_rules: int


class A11yIssueResponseV2(BaseModel):
    rule: str
    severity: str
    message: str
    wcag_criterion: str
    suggestion: str = ""
    matches: list[str] = []


class A11yResponseV2(BaseModel):
    passed: bool
    label: str
    issue_count: int
    reading_grade: float
    target_grade: float
    issues: list[A11yIssueResponseV2]


class CombinedScoreResponseV2(BaseModel):
    readability: ReadabilityResponseV2
    lint: LintResponseV2
    a11y: A11yResponseV2


# ── Helpers ──────────────────────────────────────────────────────────────────


def _build_readability_response(text: str) -> ReadabilityResponseV2:
    result = _readability_scorer.score(text)
    return ReadabilityResponseV2(**result.to_dict())


def _build_lint_response(text: str) -> LintResponseV2:
    results = _content_linter.lint(text)
    issues = [
        LintIssueV2(
            rule=r.rule,
            passed=r.passed,
            severity=r.severity.value,
            message=r.message,
            suggestion=r.suggestion,
            matches=r.matches,
        )
        for r in results
    ]
    passed_count = sum(1 for i in issues if i.passed)
    failed_count = len(issues) - passed_count
    return LintResponseV2(
        issues=issues,
        passed_count=passed_count,
        failed_count=failed_count,
        total_rules=len(issues),
    )


def _build_a11y_response(text: str) -> A11yResponseV2:
    result = _a11y_checker.check(text)
    return A11yResponseV2(
        passed=result.passed,
        label=result.label,
        issue_count=result.issue_count,
        reading_grade=result.reading_grade,
        target_grade=result.target_grade,
        issues=[
            A11yIssueResponseV2(
                rule=i.rule,
                severity=i.severity.value,
                message=i.message,
                wcag_criterion=i.wcag_criterion,
                suggestion=i.suggestion,
                matches=i.matches,
            )
            for i in result.issues
        ],
    )


# ── Routes ───────────────────────────────────────────────────────────────────


@router.post("/readability", response_model=ReadabilityResponseV2)
async def score_readability(body: ScoreRequestV2) -> ReadabilityResponseV2:
    """Score text for readability metrics."""
    try:
        return _build_readability_response(body.text)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Readability scoring failed: {exc}",
        )


@router.post("/lint", response_model=LintResponseV2)
async def score_lint(body: ScoreRequestV2) -> LintResponseV2:
    """Run the content linter on text."""
    try:
        return _build_lint_response(body.text)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Linting failed: {exc}",
        )


@router.post("/a11y", response_model=A11yResponseV2)
async def score_a11y(body: ScoreRequestV2) -> A11yResponseV2:
    """Run accessibility checks on text."""
    try:
        return _build_a11y_response(body.text)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Accessibility check failed: {exc}",
        )


@router.post("/all", response_model=CombinedScoreResponseV2)
async def score_all(body: ScoreRequestV2) -> CombinedScoreResponseV2:
    """Run all scoring tools and return a combined result."""
    try:
        return CombinedScoreResponseV2(
            readability=_build_readability_response(body.text),
            lint=_build_lint_response(body.text),
            a11y=_build_a11y_response(body.text),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Combined scoring failed: {exc}",
        )
