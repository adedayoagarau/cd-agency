"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Agent Models ──────────────────────────────────────────────────────────────


class AgentInputSchema(BaseModel):
    """Schema for an agent's expected input field."""

    name: str
    type: str
    required: bool
    description: str = ""


class AgentOutputSchema(BaseModel):
    """Schema for an agent's expected output field."""

    name: str
    type: str
    description: str = ""


class AgentSummary(BaseModel):
    """Lightweight agent representation for list endpoints."""

    slug: str
    name: str
    description: str
    tags: list[str] = []


class AgentDetail(BaseModel):
    """Full agent representation including inputs and outputs."""

    slug: str
    name: str
    description: str
    tags: list[str] = []
    inputs: list[AgentInputSchema] = []
    outputs: list[AgentOutputSchema] = []
    related_agents: list[str] = []
    version: str = "1.0.0"
    difficulty_level: str = "intermediate"


class AgentRunRequest(BaseModel):
    """Request body for running an agent."""

    input: dict[str, Any] = Field(..., description="Input fields for the agent")
    preset: str | None = Field(None, description="Optional design system preset name")
    provider: str | None = Field(None, description="LLM provider override (e.g. 'openai', 'gemini')")
    model: str | None = Field(None, description="Model override (e.g. 'gpt-4o')")


class AgentRunResponse(BaseModel):
    """Response from running an agent."""

    content: str
    agent_name: str
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0


# ── Scoring Models ────────────────────────────────────────────────────────────


class ScoreRequest(BaseModel):
    """Request body for scoring endpoints."""

    text: str = Field(..., min_length=1, description="Text content to score")


class ReadabilityResponse(BaseModel):
    """Readability scoring result."""

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


class LintIssue(BaseModel):
    """A single lint rule result."""

    rule: str
    passed: bool
    severity: str
    message: str
    suggestion: str = ""
    matches: list[str] = []


class LintResponse(BaseModel):
    """Linter result containing all rule checks."""

    issues: list[LintIssue]
    passed_count: int
    failed_count: int
    total_rules: int


class A11yIssueResponse(BaseModel):
    """A single accessibility issue."""

    rule: str
    severity: str
    message: str
    wcag_criterion: str
    suggestion: str = ""
    matches: list[str] = []


class A11yResponse(BaseModel):
    """Accessibility checker result."""

    passed: bool
    label: str
    issue_count: int
    reading_grade: float
    target_grade: float
    issues: list[A11yIssueResponse]


class CombinedScoreResponse(BaseModel):
    """Combined result from all scoring tools."""

    readability: ReadabilityResponse
    lint: LintResponse
    a11y: A11yResponse


# ── Preset Models ─────────────────────────────────────────────────────────────


class PresetSummary(BaseModel):
    """Lightweight preset representation for list endpoints."""

    name: str
    filename: str


class PresetDetail(BaseModel):
    """Full preset data."""

    name: str
    filename: str
    tone_descriptors: list[str] = []
    do: list[str] = Field(default_factory=list, alias="do_rules")
    dont: list[str] = Field(default_factory=list, alias="dont_rules")
    sample_content: list[str] = []
    character_limits: dict[str, int] = {}
    terminology: dict[str, str] = {}

    model_config = {"populate_by_name": True}


# ── Validation Models ────────────────────────────────────────────────────────


class ValidateRequest(BaseModel):
    """Request body for content validation."""

    text: str = Field(..., min_length=1, description="Text content to validate")
    element_type: str = Field(..., description="UI element type (e.g., 'button', 'toast', 'push_body')")
    platform: str | None = Field(None, description="Target platform: ios, android, web")
    target_language: str | None = Field(None, description="ISO language code for localization check (e.g., 'de', 'fr')")
    custom_limit: int | None = Field(None, description="Override the default character limit")


class ViolationResponse(BaseModel):
    """A single constraint violation."""

    rule: str
    severity: str
    message: str
    value: Any = None
    limit: Any = None


class ValidateResponse(BaseModel):
    """Content validation result."""

    passed: bool
    error_count: int
    warning_count: int
    violations: list[ViolationResponse]
    summary: str


class ElementTypeInfo(BaseModel):
    """UI element type with its character limit."""

    type: str
    max_chars: int
    label: str


# ── Content History Models ───────────────────────────────────────────────────


class VersionResponse(BaseModel):
    """A single content version entry."""

    id: str
    timestamp: float
    agent_name: str
    agent_slug: str
    input_text: str
    output_text: str
    input_fields: dict[str, str] = {}
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0


class VersionDiffResponse(BaseModel):
    """Before/after diff for a content version."""

    id: str
    agent: str
    timestamp: float
    before: str
    after: str
    before_len: int
    after_len: int
    char_delta: int


class HistoryStatsResponse(BaseModel):
    """Aggregate stats for content version history."""

    count: int
    agents_used: list[str]
    latest: dict[str, Any] | None = None


# ── Conversation Models ────────────────────────────────────────────────────


class ConversationMessage(BaseModel):
    """A single message in a multi-turn conversation."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ConversationRequest(BaseModel):
    """Request body for multi-turn agent conversation."""

    messages: list[ConversationMessage] = Field(
        ..., min_length=1, description="Conversation history"
    )
    preset: str | None = Field(None, description="Optional design system preset name")


class ConversationResponse(BaseModel):
    """Response from a multi-turn conversation."""

    content: str
    agent_name: str
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0


# ── Workflow Models ────────────────────────────────────────────────────────


class WorkflowStepSchema(BaseModel):
    """Schema for a single workflow step."""

    name: str
    agent: str
    parallel_group: str | None = None
    condition: str | None = None


class WorkflowSummary(BaseModel):
    """Lightweight workflow for list endpoints."""

    slug: str
    name: str
    description: str
    step_count: int


class WorkflowDetail(BaseModel):
    """Full workflow with step definitions."""

    slug: str
    name: str
    description: str
    steps: list[WorkflowStepSchema]


class WorkflowRunRequest(BaseModel):
    """Request body for running a workflow."""

    input: dict[str, Any] = Field(..., description="Workflow input fields")


class StepResultResponse(BaseModel):
    """Result from a single workflow step."""

    step_name: str
    agent_name: str
    output: str
    skipped: bool = False
    error: str | None = None


class WorkflowRunResponse(BaseModel):
    """Response from running a workflow."""

    workflow_name: str
    steps: list[StepResultResponse]
    final_output: str
    total_tokens: int = 0
    latency_ms: float = 0.0


# ── Scrape Models ──────────────────────────────────────────────────────────


class ScrapeRequest(BaseModel):
    """Request body for web page scraping."""

    url: str = Field(..., description="URL to scrape")


class ScrapeResponse(BaseModel):
    """Structured content extracted from a web page."""

    url: str
    title: str = ""
    description: str = ""
    headings: list[str] = []
    paragraphs: list[str] = []
    links: list[str] = []
    images: list[str] = []
    meta: dict[str, str] = {}
    raw_text: str = ""


# ── Export Models ──────────────────────────────────────────────────────────


class ExportEntry(BaseModel):
    """A single content entry for export."""

    id: str = ""
    source: str
    target: str
    context: str = ""
    agent: str = ""
    notes: str = ""


class ExportRequest(BaseModel):
    """Request body for content export."""

    entries: list[ExportEntry] = Field(..., min_length=1)
    format: str = Field(..., description="Export format: json, csv, markdown, xliff")


# ── Batch Models ───────────────────────────────────────────────────────────


class BatchItem(BaseModel):
    """A single item in a batch request."""

    input: dict[str, Any] = Field(..., description="Input fields for one agent run")


class BatchRequest(BaseModel):
    """Request body for batch agent execution."""

    items: list[BatchItem] = Field(..., min_length=1, max_length=50)
    preset: str | None = Field(None, description="Optional design system preset")
