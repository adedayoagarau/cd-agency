"""Enhanced multi-agent orchestration with shared context and handoffs.

Extends the existing WorkflowEngine with:
- SharedContext that accumulates state across agents
- AgentHandoff protocol for explicit inter-agent instructions
- Dynamic routing based on intermediate quality scores
- Pipeline-level memory and decision tracking
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

from runtime.agent import Agent, AgentOutput


@dataclass
class AgentHandoff:
    """Instructions from one agent to the next."""

    from_agent: str
    to_agent: str
    instructions: str = ""
    focus_areas: list[str] = field(default_factory=list)
    findings: dict[str, Any] = field(default_factory=dict)
    quality_scores: dict[str, float] = field(default_factory=dict)
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()

    def build_context_block(self) -> str:
        """Format handoff as context for the receiving agent's prompt."""
        parts = [f"## Handoff from {self.from_agent}\n"]

        if self.instructions:
            parts.append(f"Instructions: {self.instructions}\n")

        if self.focus_areas:
            parts.append("Focus areas:")
            for area in self.focus_areas:
                parts.append(f"  - {area}")
            parts.append("")

        if self.findings:
            parts.append("Findings from previous analysis:")
            for key, value in self.findings.items():
                parts.append(f"  - {key}: {value}")
            parts.append("")

        if self.quality_scores:
            parts.append("Quality scores so far:")
            for metric, score in self.quality_scores.items():
                parts.append(f"  - {metric}: {score}")

        return "\n".join(parts)


@dataclass
class SharedContext:
    """Mutable state shared across all agents in a pipeline."""

    pipeline_name: str = ""
    decisions: list[dict[str, Any]] = field(default_factory=list)
    accumulated_findings: dict[str, Any] = field(default_factory=dict)
    terminology_updates: dict[str, str] = field(default_factory=dict)
    quality_scores: dict[str, dict[str, float]] = field(default_factory=dict)
    handoffs: list[AgentHandoff] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def record_decision(self, agent: str, decision: str, reasoning: str = "") -> None:
        """Record a decision made during pipeline execution."""
        self.decisions.append({
            "agent": agent,
            "decision": decision,
            "reasoning": reasoning,
            "timestamp": time.time(),
        })

    def record_finding(self, agent: str, key: str, value: Any) -> None:
        """Record a finding from an agent's analysis."""
        self.accumulated_findings[key] = {
            "value": value,
            "source_agent": agent,
            "timestamp": time.time(),
        }

    def record_quality(self, agent: str, scores: dict[str, float]) -> None:
        """Record quality scores from an agent's evaluation."""
        self.quality_scores[agent] = scores

    def add_handoff(self, handoff: AgentHandoff) -> None:
        """Add a handoff to the chain."""
        self.handoffs.append(handoff)

    def get_latest_handoff(self) -> AgentHandoff | None:
        """Get the most recent handoff."""
        return self.handoffs[-1] if self.handoffs else None

    def build_context_block(self) -> str:
        """Build accumulated context for injection into agent prompts."""
        if not self.decisions and not self.accumulated_findings and not self.terminology_updates:
            return ""

        parts = ["## Pipeline Context\n"]

        if self.decisions:
            parts.append("### Decisions Made")
            for d in self.decisions[-5:]:
                parts.append(f"- [{d['agent']}] {d['decision']}")
            parts.append("")

        if self.accumulated_findings:
            parts.append("### Key Findings")
            for key, info in list(self.accumulated_findings.items())[-10:]:
                parts.append(f"- {key}: {info['value']} (from {info['source_agent']})")
            parts.append("")

        if self.terminology_updates:
            parts.append("### Terminology Decisions")
            for term, preferred in list(self.terminology_updates.items())[-10:]:
                parts.append(f"- Use \"{preferred}\" (not \"{term}\")")
            parts.append("")

        if self.quality_scores:
            parts.append("### Quality Scores")
            for agent_name, scores in self.quality_scores.items():
                score_str = ", ".join(f"{k}: {v:.0f}" for k, v in scores.items())
                parts.append(f"- {agent_name}: {score_str}")

        return "\n".join(parts)


@dataclass
class RoutingRule:
    """Dynamic routing rule — choose next agent based on conditions."""

    condition: Callable[[dict[str, Any]], bool]
    target_agent: str
    description: str = ""


@dataclass
class PipelineStep:
    """A step in an orchestrated pipeline."""

    agent_slug: str
    input_map: dict[str, str] = field(default_factory=dict)
    handoff_instructions: str = ""
    focus_areas: list[str] = field(default_factory=list)
    routing_rules: list[RoutingRule] = field(default_factory=list)
    skip_if: Callable[[SharedContext], bool] | None = None


@dataclass
class StepOutput:
    """Result from a single orchestrated step."""

    step_index: int
    agent_name: str
    agent_slug: str
    output: AgentOutput
    handoff: AgentHandoff | None = None
    skipped: bool = False
    error: str | None = None
    duration_ms: float = 0.0


@dataclass
class PipelineResult:
    """Complete result from an orchestrated pipeline."""

    pipeline_name: str
    steps: list[StepOutput] = field(default_factory=list)
    shared_context: SharedContext = field(default_factory=SharedContext)
    total_duration_ms: float = 0.0
    dynamic_steps_added: int = 0

    @property
    def final_output(self) -> str:
        """Content from the last successful step."""
        for step in reversed(self.steps):
            if not step.skipped and step.output and step.output.content:
                return step.output.content
        return ""

    @property
    def all_outputs(self) -> dict[str, str]:
        """All step outputs keyed by agent slug."""
        return {
            s.agent_slug: s.output.content
            for s in self.steps
            if not s.skipped and s.output
        }

    @property
    def total_tokens(self) -> dict[str, int]:
        """Total token usage across all steps."""
        input_tokens = sum(s.output.input_tokens for s in self.steps if s.output)
        output_tokens = sum(s.output.output_tokens for s in self.steps if s.output)
        return {"input": input_tokens, "output": output_tokens, "total": input_tokens + output_tokens}

    @property
    def handoff_chain(self) -> list[AgentHandoff]:
        """All handoffs in execution order."""
        return [s.handoff for s in self.steps if s.handoff]


class OrchestratedPipeline:
    """Multi-agent pipeline with shared context and real handoffs.

    Unlike WorkflowEngine (which resolves string references), this pipeline:
    - Maintains a SharedContext that accumulates state across agents
    - Supports AgentHandoff protocol for explicit inter-agent instructions
    - Enables dynamic routing based on intermediate quality scores
    - Injects accumulated context into each agent's system prompt
    """

    def __init__(
        self,
        name: str,
        steps: list[PipelineStep],
        *,
        description: str = "",
        max_dynamic_steps: int = 3,
        on_step_start: Callable[[int, str], None] | None = None,
        on_step_complete: Callable[[int, str, StepOutput], None] | None = None,
    ) -> None:
        self.name = name
        self.steps = list(steps)
        self.description = description
        self.max_dynamic_steps = max_dynamic_steps
        self.on_step_start = on_step_start
        self.on_step_complete = on_step_complete

    def run(
        self,
        runner: Any,
        registry: Any,
        initial_input: dict[str, Any],
        *,
        shared_context: SharedContext | None = None,
    ) -> PipelineResult:
        """Execute the pipeline with shared context and handoffs.

        Args:
            runner: AgentRunner instance.
            registry: AgentRegistry for looking up agents.
            initial_input: Initial user input for the first step.
            shared_context: Optional pre-populated shared context.

        Returns:
            PipelineResult with all outputs, handoffs, and shared context.
        """
        start_time = time.monotonic()
        context = shared_context or SharedContext(pipeline_name=self.name)
        result = PipelineResult(pipeline_name=self.name, shared_context=context)

        current_content = initial_input.get("content", "")
        previous_output: AgentOutput | None = None
        dynamic_steps_added = 0

        steps_to_run = list(self.steps)
        step_index = 0

        while step_index < len(steps_to_run):
            step = steps_to_run[step_index]

            # Check skip condition
            if step.skip_if and step.skip_if(context):
                step_output = StepOutput(
                    step_index=step_index,
                    agent_name=step.agent_slug,
                    agent_slug=step.agent_slug,
                    output=AgentOutput(content="", agent_name=step.agent_slug),
                    skipped=True,
                )
                result.steps.append(step_output)
                step_index += 1
                continue

            # Look up agent
            agent = registry.get(step.agent_slug)
            if agent is None:
                step_output = StepOutput(
                    step_index=step_index,
                    agent_name=step.agent_slug,
                    agent_slug=step.agent_slug,
                    output=AgentOutput(content="", agent_name=step.agent_slug),
                    error=f"Agent not found: {step.agent_slug}",
                )
                result.steps.append(step_output)
                step_index += 1
                continue

            if self.on_step_start:
                self.on_step_start(step_index, agent.name)

            # Build input for this step
            step_input = self._build_step_input(
                step, agent, initial_input, current_content, context
            )

            # Execute
            step_start = time.monotonic()
            try:
                output = runner.run(agent, step_input)
            except Exception as e:
                step_output = StepOutput(
                    step_index=step_index,
                    agent_name=agent.name,
                    agent_slug=step.agent_slug,
                    output=AgentOutput(content="", agent_name=agent.name),
                    error=str(e),
                    duration_ms=(time.monotonic() - step_start) * 1000,
                )
                result.steps.append(step_output)
                if self.on_step_complete:
                    self.on_step_complete(step_index, agent.name, step_output)
                step_index += 1
                continue

            step_duration = (time.monotonic() - step_start) * 1000

            # Update current content for next step
            if output.content:
                current_content = output.content

            # Score the output using existing tools
            scores = self._score_output(output.content)
            context.record_quality(agent.name, scores)

            # Create handoff for next step
            handoff = self._create_handoff(
                agent, step, output, scores, steps_to_run, step_index
            )
            if handoff:
                context.add_handoff(handoff)

            step_output = StepOutput(
                step_index=step_index,
                agent_name=agent.name,
                agent_slug=step.agent_slug,
                output=output,
                handoff=handoff,
                duration_ms=step_duration,
            )
            result.steps.append(step_output)

            if self.on_step_complete:
                self.on_step_complete(step_index, agent.name, step_output)

            # Check dynamic routing rules
            if dynamic_steps_added < self.max_dynamic_steps:
                for rule in step.routing_rules:
                    rule_context = {
                        "scores": scores,
                        "content": output.content,
                        "agent": agent.name,
                        "step_index": step_index,
                        "shared_context": context,
                    }
                    if rule.condition(rule_context):
                        dynamic_step = PipelineStep(
                            agent_slug=rule.target_agent,
                            handoff_instructions=rule.description,
                        )
                        # Insert after current position
                        steps_to_run.insert(step_index + 1, dynamic_step)
                        dynamic_steps_added += 1
                        context.record_decision(
                            agent.name,
                            f"Routed to {rule.target_agent}",
                            rule.description,
                        )
                        break  # Only one dynamic route per step

            previous_output = output
            step_index += 1

        result.total_duration_ms = (time.monotonic() - start_time) * 1000
        result.dynamic_steps_added = dynamic_steps_added
        return result

    def _build_step_input(
        self,
        step: PipelineStep,
        agent: Agent,
        initial_input: dict[str, Any],
        current_content: str,
        context: SharedContext,
    ) -> dict[str, Any]:
        """Build the input dict for a step, including handoff context."""
        # Start with the content from previous step
        step_input: dict[str, Any] = {}

        # Map inputs — use step's input_map or default to primary input
        if step.input_map:
            for field_name, source in step.input_map.items():
                if source.startswith("$input."):
                    step_input[field_name] = initial_input.get(source[7:], "")
                elif source == "$content":
                    step_input[field_name] = current_content
                else:
                    step_input[field_name] = source
        else:
            # Default: pass current content as the primary input
            if agent.inputs:
                step_input[agent.inputs[0].name] = current_content

        # Inject shared context and handoff into the content
        context_block = context.build_context_block()
        handoff = context.get_latest_handoff()
        handoff_block = handoff.build_context_block() if handoff else ""

        # Append context to the primary input field
        if agent.inputs and agent.inputs[0].name in step_input:
            primary_key = agent.inputs[0].name
            primary_value = step_input[primary_key]
            extra = []
            if handoff_block:
                extra.append(handoff_block)
            if context_block:
                extra.append(context_block)
            if extra:
                step_input[primary_key] = primary_value + "\n\n" + "\n\n".join(extra)

        return step_input

    def _score_output(self, content: str) -> dict[str, float]:
        """Score content using existing tools (best-effort)."""
        scores: dict[str, float] = {}

        try:
            from tools.readability import analyze
            result = analyze(content)
            scores["readability"] = result.get("flesch_reading_ease", 0)
        except Exception:
            pass

        try:
            from tools.linter import lint
            issues = lint(content)
            scores["lint_issues"] = len(issues) if isinstance(issues, list) else 0
        except Exception:
            pass

        return scores

    def _create_handoff(
        self,
        agent: Agent,
        step: PipelineStep,
        output: AgentOutput,
        scores: dict[str, float],
        all_steps: list[PipelineStep],
        current_index: int,
    ) -> AgentHandoff | None:
        """Create a handoff for the next step."""
        if current_index >= len(all_steps) - 1:
            return None

        next_step = all_steps[current_index + 1]

        return AgentHandoff(
            from_agent=agent.name,
            to_agent=next_step.agent_slug,
            instructions=step.handoff_instructions or f"Review and improve the output from {agent.name}.",
            focus_areas=step.focus_areas,
            findings={},
            quality_scores=scores,
        )


# ---------------------------------------------------------------------------
# Pre-built pipeline templates
# ---------------------------------------------------------------------------

def content_quality_pipeline() -> OrchestratedPipeline:
    """Pre-built pipeline: draft → review → accessibility → polish."""
    return OrchestratedPipeline(
        name="Content Quality Pipeline",
        steps=[
            PipelineStep(
                agent_slug="content-designer-generalist",
                handoff_instructions="Draft initial content based on the input.",
            ),
            PipelineStep(
                agent_slug="microcopy-review-agent",
                handoff_instructions="Review the draft for clarity, brevity, and UX best practices.",
                focus_areas=["clarity", "brevity", "actionability"],
            ),
            PipelineStep(
                agent_slug="accessibility-content-auditor",
                handoff_instructions="Check for accessibility issues and suggest fixes.",
                focus_areas=["screen reader compatibility", "plain language", "WCAG compliance"],
                routing_rules=[
                    RoutingRule(
                        condition=lambda ctx: ctx.get("scores", {}).get("readability", 100) < 60,
                        target_agent="privacy-legal-content-simplifier",
                        description="Readability is low — route to simplifier for plain language rewrite.",
                    ),
                ],
            ),
            PipelineStep(
                agent_slug="tone-evaluation-agent",
                handoff_instructions="Evaluate tone consistency and suggest adjustments.",
            ),
        ],
        description="Full content quality pipeline with dynamic routing.",
    )


def error_message_pipeline() -> OrchestratedPipeline:
    """Pre-built pipeline: draft error → validate tone → check a11y → optimize for mobile."""
    return OrchestratedPipeline(
        name="Error Message Pipeline",
        steps=[
            PipelineStep(
                agent_slug="error-message-architect",
                handoff_instructions="Draft user-friendly error messages.",
            ),
            PipelineStep(
                agent_slug="tone-evaluation-agent",
                handoff_instructions="Validate the error message tone — should be helpful, not blaming.",
                focus_areas=["empathy", "clarity", "actionability"],
            ),
            PipelineStep(
                agent_slug="accessibility-content-auditor",
                handoff_instructions="Check error messages for accessibility compliance.",
            ),
            PipelineStep(
                agent_slug="mobile-ux-writer",
                handoff_instructions="Optimize error messages for mobile display constraints.",
                focus_areas=["character count", "touch target labels", "responsive text"],
            ),
        ],
        description="End-to-end error message creation pipeline.",
    )


def localization_pipeline() -> OrchestratedPipeline:
    """Pre-built pipeline: audit → simplify → validate."""
    return OrchestratedPipeline(
        name="Localization Prep Pipeline",
        steps=[
            PipelineStep(
                agent_slug="content-consistency-checker",
                handoff_instructions="Audit content for consistency issues before localization.",
            ),
            PipelineStep(
                agent_slug="localization-content-strategist",
                handoff_instructions="Prepare content for internationalization.",
                focus_areas=["cultural sensitivity", "translatable text", "variable placement"],
            ),
            PipelineStep(
                agent_slug="accessibility-content-auditor",
                handoff_instructions="Final accessibility check on localization-ready content.",
            ),
        ],
        description="Prepare content for localization with consistency and a11y checks.",
    )
