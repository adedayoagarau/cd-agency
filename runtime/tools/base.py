"""Base Tool class for the agent tool framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Result from executing a tool."""

    success: bool
    data: Any = None
    error: str = ""

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"success": self.success}
        if self.data is not None:
            d["data"] = self.data
        if self.error:
            d["error"] = self.error
        return d

    def to_content_string(self) -> str:
        """Format as a string suitable for injecting into LLM messages."""
        if not self.success:
            return f"Tool error: {self.error}"
        if isinstance(self.data, str):
            return self.data
        if isinstance(self.data, dict):
            import json
            return json.dumps(self.data, indent=2, default=str)
        return str(self.data)


class Tool(ABC):
    """Base class for tools that agents can call."""

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {}

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given parameters."""

    def to_llm_tool_schema(self) -> dict[str, Any]:
        """Convert to Anthropic/OpenAI function-calling schema.

        Returns a schema compatible with both providers:
        - Anthropic: {"name", "description", "input_schema"}
        - OpenAI:    {"type": "function", "function": {"name", "description", "parameters"}}
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters,
                "required": [
                    k for k, v in self.parameters.items()
                    if not v.get("optional", False)
                ],
            },
        }

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function-calling format."""
        schema = self.to_llm_tool_schema()
        return {
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": schema["input_schema"],
            },
        }

    def __repr__(self) -> str:
        return f"Tool(name={self.name!r})"
