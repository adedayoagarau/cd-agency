"""Configuration management for the CD Agency runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


CONFIG_FILENAMES = [".cd-agency.yaml", ".cd-agency.yml", "cd-agency.yaml"]


@dataclass
class Config:
    """Runtime configuration with config file and environment variable overrides.

    Priority (highest to lowest):
    1. Environment variables
    2. Config file (.cd-agency.yaml)
    3. Defaults
    """

    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"
    agents_dir: Path = field(default_factory=lambda: Path("content-design"))
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: float = 60.0
    max_retries: int = 3
    default_preset: str = ""
    brand_voice_guide: str = ""
    output_format: str = "text"  # text, json, markdown

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from config file + environment variables."""
        # Start with config file values
        file_config = cls._load_config_file()

        # Environment variables override config file
        agents_dir_str = os.environ.get(
            "CD_AGENCY_AGENTS_DIR",
            file_config.get("agents_dir", "content-design"),
        )
        return cls(
            api_key=os.environ.get(
                "ANTHROPIC_API_KEY",
                file_config.get("api_key", ""),
            ),
            model=os.environ.get(
                "CD_AGENCY_MODEL",
                file_config.get("model", "claude-sonnet-4-20250514"),
            ),
            agents_dir=Path(agents_dir_str),
            max_tokens=int(os.environ.get(
                "CD_AGENCY_MAX_TOKENS",
                file_config.get("max_tokens", 4096),
            )),
            temperature=float(os.environ.get(
                "CD_AGENCY_TEMPERATURE",
                file_config.get("temperature", 0.7),
            )),
            default_preset=file_config.get("default_preset", ""),
            brand_voice_guide=file_config.get("brand_voice_guide", ""),
            output_format=file_config.get("output_format", "text"),
        )

    @staticmethod
    def _load_config_file() -> dict:
        """Search for and load a config file."""
        for filename in CONFIG_FILENAMES:
            path = Path(filename)
            if path.exists():
                with open(path) as f:
                    data = yaml.safe_load(f) or {}
                return data
        return {}

    def validate(self) -> list[str]:
        """Return a list of configuration errors, empty if valid."""
        errors = []
        if not self.api_key:
            errors.append("ANTHROPIC_API_KEY is not set")
        if not self.agents_dir.exists():
            errors.append(f"Agents directory not found: {self.agents_dir}")
        return errors
