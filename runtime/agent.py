"""Core Agent model and output types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentInput:
    """Defines an expected input field for an agent."""

    name: str
    type: str
    required: bool = True
    description: str = ""


@dataclass
class AgentOutput:
    """Structured output from an agent execution."""

    content: str
    agent_name: str
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    raw_response: Any = None


@dataclass
class OutputField:
    """Defines an expected output field for an agent."""

    name: str
    type: str
    description: str = ""


@dataclass
class Agent:
    """A content design agent loaded from a markdown definition file."""

    name: str
    description: str
    color: str = ""
    version: str = "1.0.0"
    difficulty_level: str = "intermediate"
    tags: list[str] = field(default_factory=list)
    inputs: list[AgentInput] = field(default_factory=list)
    outputs: list[OutputField] = field(default_factory=list)
    related_agents: list[str] = field(default_factory=list)

    # Prompt components
    system_prompt: str = ""
    few_shot_examples: str = ""
    core_mission: str = ""
    critical_rules: str = ""
    technical_deliverables: str = ""
    workflow_process: str = ""
    success_metrics: str = ""

    # Knowledge references (paths relative to knowledge/ dir, e.g. "foundations/plain-language")
    knowledge_refs: list[str] = field(default_factory=list)
    # Resolved knowledge content (populated by loader)
    knowledge_content: str = ""

    # Source
    source_file: str = ""

    @property
    def slug(self) -> str:
        """URL-friendly identifier derived from source filename."""
        if self.source_file:
            from pathlib import Path
            return Path(self.source_file).stem
        return self.name.lower().replace(" ", "-").replace("&", "and")

    def build_system_message(self) -> str:
        """Compose the full system message from agent components."""
        parts = []

        if self.system_prompt:
            parts.append(self.system_prompt)

        if self.knowledge_content:
            parts.append(f"## Knowledge Base\n\nApply the following content design knowledge when generating recommendations:\n\n{self.knowledge_content}")

        if self.few_shot_examples:
            parts.append(self.few_shot_examples)

        if self.critical_rules:
            parts.append(f"## Critical Rules\n\n{self.critical_rules}")

        return "\n\n---\n\n".join(parts)

    def build_user_message(self, user_input: dict[str, Any]) -> str:
        """Compose the user message from structured input."""
        parts = []
        for key, value in user_input.items():
            if value is not None and value != "":
                label = key.replace("_", " ").title()
                parts.append(f"**{label}:** {value}")
        return "\n".join(parts)

    def validate_input(self, user_input: dict[str, Any]) -> list[str]:
        """Validate user input against agent's defined inputs. Returns list of errors."""
        errors = []
        for inp in self.inputs:
            if inp.required and inp.name not in user_input:
                errors.append(f"Missing required input: '{inp.name}' — {inp.description}")
            elif inp.required and not user_input.get(inp.name):
                errors.append(f"Empty required input: '{inp.name}' — {inp.description}")
        return errors

    def get_required_inputs(self) -> list[AgentInput]:
        """Return only the required inputs."""
        return [i for i in self.inputs if i.required]

    def get_optional_inputs(self) -> list[AgentInput]:
        """Return only the optional inputs."""
        return [i for i in self.inputs if not i.required]

    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', slug='{self.slug}', tags={self.tags})"
