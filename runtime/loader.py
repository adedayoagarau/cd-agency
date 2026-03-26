"""Agent loader — parses markdown agent files into Agent objects."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from runtime.agent import Agent, AgentInput, OutputField
from runtime.knowledge import resolve_knowledge_refs, DEFAULT_KNOWLEDGE_DIR


def load_agent(filepath: Path, knowledge_dir: Path | None = None) -> Agent:
    """Load a single agent from a markdown file.

    Parses YAML frontmatter and markdown sections into an Agent object.
    """
    text = filepath.read_text(encoding="utf-8")

    # Parse YAML frontmatter
    frontmatter, body = _parse_frontmatter(text)

    # Parse markdown sections
    sections = _parse_sections(body)

    # Build input definitions
    inputs = []
    for inp in frontmatter.get("inputs", []):
        inputs.append(AgentInput(
            name=inp.get("name", ""),
            type=inp.get("type", "string"),
            required=inp.get("required", True),
            description=inp.get("description", ""),
        ))

    # Build output definitions
    outputs = []
    for out in frontmatter.get("outputs", []):
        outputs.append(OutputField(
            name=out.get("name", ""),
            type=out.get("type", "string"),
            description=out.get("description", ""),
        ))

    # Resolve knowledge references
    knowledge_refs = frontmatter.get("knowledge", [])
    kdir = knowledge_dir or DEFAULT_KNOWLEDGE_DIR
    knowledge_content = resolve_knowledge_refs(knowledge_refs, kdir)

    return Agent(
        name=frontmatter.get("name", filepath.stem),
        description=frontmatter.get("description", ""),
        color=frontmatter.get("color", ""),
        version=frontmatter.get("version", "1.0.0"),
        difficulty_level=frontmatter.get("difficulty_level", "intermediate"),
        tags=frontmatter.get("tags", []),
        inputs=inputs,
        outputs=outputs,
        related_agents=frontmatter.get("related_agents", []),
        preferred_model=frontmatter.get("model", ""),
        available_tools=frontmatter.get("tools", []),
        system_prompt=sections.get("system prompt", ""),
        few_shot_examples=sections.get("few-shot examples", ""),
        core_mission=sections.get("core mission", ""),
        critical_rules=sections.get("critical rules", ""),
        technical_deliverables=sections.get("technical deliverables", ""),
        workflow_process=sections.get("workflow process", ""),
        success_metrics=sections.get("success metrics", ""),
        knowledge_refs=knowledge_refs,
        knowledge_content=knowledge_content,
        source_file=str(filepath),
    )


def load_agents_from_directory(directory: Path) -> list[Agent]:
    """Load all agent files from a directory.

    Scans for .md files and parses each one into an Agent object.
    """
    agents = []
    if not directory.exists():
        return agents

    for filepath in sorted(directory.glob("*.md")):
        try:
            agent = load_agent(filepath)
            agents.append(agent)
        except Exception as e:
            # Log but don't fail on individual agent parse errors
            print(f"Warning: Failed to load {filepath.name}: {e}")

    return agents


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and remaining body from markdown text."""
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)"
    match = re.match(pattern, text, re.DOTALL)

    if not match:
        return {}, text

    frontmatter_str = match.group(1)
    body = match.group(2)

    try:
        frontmatter = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        frontmatter = {}

    return frontmatter, body


def _parse_sections(body: str) -> dict[str, str]:
    """Parse markdown body into named sections by ### headers."""
    sections: dict[str, str] = {}
    current_section = ""
    current_content: list[str] = []

    for line in body.split("\n"):
        header_match = re.match(r"^###\s+(.+)$", line)
        if header_match:
            # Save previous section
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = header_match.group(1).strip().lower()
            current_content = []
        else:
            current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections
