"""Design system integration for content constraint validation.

Loads design system specifications (from YAML config or Figma-style tokens)
and provides component-level content constraints to agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ComponentConstraint:
    """Content constraint for a design system component."""

    component: str
    element: str  # maps to constraints.ELEMENT_CHAR_LIMITS keys
    max_chars: int
    min_chars: int = 0
    max_lines: int = 0
    notes: str = ""
    platform_overrides: dict[str, int] = field(default_factory=dict)

    def get_limit(self, platform: str | None = None) -> int:
        """Get the character limit, applying platform override if available."""
        if platform and platform in self.platform_overrides:
            return self.platform_overrides[platform]
        return self.max_chars


@dataclass
class DesignSystem:
    """A design system specification with component constraints."""

    name: str
    version: str = ""
    description: str = ""
    default_platform: str = "web"
    capitalization: str = "sentence"  # "sentence", "title", "upper"
    components: list[ComponentConstraint] = field(default_factory=list)
    terminology: dict[str, str] = field(default_factory=dict)  # preferred → avoid
    voice_principles: list[str] = field(default_factory=list)

    def get_component(self, name: str) -> ComponentConstraint | None:
        """Find a component constraint by name."""
        for c in self.components:
            if c.component == name:
                return c
        return None

    def get_components_by_element(self, element: str) -> list[ComponentConstraint]:
        """Find all components that map to a given element type."""
        return [c for c in self.components if c.element == element]

    def build_context_block(self) -> str:
        """Build a context block for injection into agent prompts."""
        parts = [f"## Design System: {self.name}\n"]

        if self.description:
            parts.append(f"{self.description}\n")

        parts.append(f"**Default capitalization:** {self.capitalization} case")
        parts.append(f"**Default platform:** {self.default_platform}\n")

        if self.components:
            parts.append("**Component Constraints:**")
            for c in self.components:
                line = f"- **{c.component}** ({c.element}): {c.max_chars} chars max"
                if c.max_lines:
                    line += f", {c.max_lines} lines max"
                if c.notes:
                    line += f" — {c.notes}"
                parts.append(line)
            parts.append("")

        if self.terminology:
            parts.append("**Terminology Rules:**")
            for preferred, avoid in self.terminology.items():
                parts.append(f'- Use "{preferred}" (not "{avoid}")')
            parts.append("")

        if self.voice_principles:
            parts.append("**Voice Principles:**")
            for p in self.voice_principles:
                parts.append(f"- {p}")

        parts.append(
            "\nApply these design system constraints to all content. "
            "Flag any violations in your output."
        )
        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Export as a dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "default_platform": self.default_platform,
            "capitalization": self.capitalization,
            "components": [
                {
                    "component": c.component,
                    "element": c.element,
                    "max_chars": c.max_chars,
                    "min_chars": c.min_chars,
                    "max_lines": c.max_lines,
                    "notes": c.notes,
                    "platform_overrides": c.platform_overrides,
                }
                for c in self.components
            ],
            "terminology": self.terminology,
            "voice_principles": self.voice_principles,
        }


def load_design_system(filepath: Path) -> DesignSystem:
    """Load a design system spec from a YAML file.

    Expected format:
    ```yaml
    name: "My Design System"
    version: "2.0"
    description: "Component content constraints"
    default_platform: web
    capitalization: sentence

    components:
      - component: PrimaryButton
        element: button
        max_chars: 20
        notes: "Single action verb + object"
      - component: DialogTitle
        element: modal_headline
        max_chars: 50
        max_lines: 2

    terminology:
      Save: Submit
      Settings: Preferences
      Sign in: Log in

    voice_principles:
      - "Be concise — every word must earn its place"
      - "Use active voice"
    ```
    """
    text = filepath.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}

    components = []
    for comp in data.get("components", []):
        components.append(ComponentConstraint(
            component=comp.get("component", ""),
            element=comp.get("element", ""),
            max_chars=comp.get("max_chars", 0),
            min_chars=comp.get("min_chars", 0),
            max_lines=comp.get("max_lines", 0),
            notes=comp.get("notes", ""),
            platform_overrides=comp.get("platform_overrides", {}),
        ))

    return DesignSystem(
        name=data.get("name", filepath.stem),
        version=data.get("version", ""),
        description=data.get("description", ""),
        default_platform=data.get("default_platform", "web"),
        capitalization=data.get("capitalization", "sentence"),
        components=components,
        terminology=data.get("terminology", {}),
        voice_principles=data.get("voice_principles", []),
    )


def load_design_system_from_config() -> DesignSystem | None:
    """Try to load a design system from .cd-agency.yaml config."""
    config_paths = [Path(".cd-agency.yaml"), Path(".cd-agency.yml"), Path("cd-agency.yaml")]

    for config_path in config_paths:
        if config_path.exists():
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            ds_path = data.get("design_system")
            if ds_path:
                filepath = Path(ds_path)
                if filepath.exists():
                    return load_design_system(filepath)
    return None
