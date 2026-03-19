"""Configuration management for the CD Agency runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


CONFIG_FILENAMES = [".cd-agency.yaml", ".cd-agency.yml", "cd-agency.yaml"]


@dataclass
class ProductContext:
    """Product-level context injected into every agent prompt."""

    product_name: str = ""
    description: str = ""
    domain: str = ""
    audience: str = ""
    tone: str = ""
    platform: str = ""
    guidelines: list[str] = field(default_factory=list)

    def is_configured(self) -> bool:
        """Return True if any context field is set."""
        return bool(self.product_name or self.description or self.domain)

    def build_context_block(self) -> str:
        """Build a context block for injection into agent system prompts."""
        if not self.is_configured():
            return ""

        parts = ["## Product Context\n"]

        if self.product_name:
            parts.append(f"**Product:** {self.product_name}")
        if self.description:
            parts.append(f"**Description:** {self.description}")
        if self.domain:
            parts.append(f"**Domain:** {self.domain}")
        if self.audience:
            parts.append(f"**Target Audience:** {self.audience}")
        if self.tone:
            parts.append(f"**Tone & Voice:** {self.tone}")
        if self.platform:
            parts.append(f"**Platform:** {self.platform}")
        if self.guidelines:
            parts.append("\n**Content Guidelines:**")
            for g in self.guidelines:
                parts.append(f"- {g}")

        parts.append(
            "\nUse this product context to tailor all suggestions, "
            "examples, and language to this specific product and audience."
        )
        return "\n".join(parts)

    @classmethod
    def from_dict(cls, data: dict) -> ProductContext:
        """Create from a dictionary (e.g. parsed from YAML)."""
        return cls(
            product_name=data.get("product_name", ""),
            description=data.get("description", ""),
            domain=data.get("domain", ""),
            audience=data.get("audience", ""),
            tone=data.get("tone", ""),
            platform=data.get("platform", ""),
            guidelines=data.get("guidelines", []),
        )

    def to_dict(self) -> dict:
        """Export as a dictionary."""
        d: dict = {}
        if self.product_name:
            d["product_name"] = self.product_name
        if self.description:
            d["description"] = self.description
        if self.domain:
            d["domain"] = self.domain
        if self.audience:
            d["audience"] = self.audience
        if self.tone:
            d["tone"] = self.tone
        if self.platform:
            d["platform"] = self.platform
        if self.guidelines:
            d["guidelines"] = self.guidelines
        return d


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
    product_context: ProductContext = field(default_factory=ProductContext)
    provider: str = "anthropic"
    provider_keys: dict[str, str] = field(default_factory=dict)
    base_url: str = ""  # custom base URL override

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
        # Load product context
        context_data = file_config.get("product_context", {})
        product_context = ProductContext.from_dict(context_data) if context_data else ProductContext()

        # Build provider keys from env vars and config file
        provider_keys: dict[str, str] = file_config.get("provider_keys", {})
        # Map well-known env vars to provider keys
        _key_env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "kimi": "KIMI_API_KEY",
        }
        for prov, env_var in _key_env_map.items():
            env_val = os.environ.get(env_var, "")
            if env_val:
                provider_keys[prov] = env_val

        # Resolve active provider
        provider = os.environ.get(
            "CD_AGENCY_PROVIDER",
            file_config.get("provider", "anthropic"),
        )

        # Resolve API key: provider-specific key takes priority
        api_key = provider_keys.get(provider, "")
        if not api_key:
            # Fallback to ANTHROPIC_API_KEY for backward compat
            api_key = os.environ.get("ANTHROPIC_API_KEY", file_config.get("api_key", ""))

        return cls(
            api_key=api_key,
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
            timeout=float(os.environ.get(
                "CD_AGENCY_TIMEOUT",
                file_config.get("timeout", 60.0),
            )),
            max_retries=int(os.environ.get(
                "CD_AGENCY_MAX_RETRIES",
                file_config.get("max_retries", 3),
            )),
            default_preset=file_config.get("default_preset", ""),
            brand_voice_guide=file_config.get("brand_voice_guide", ""),
            output_format=file_config.get("output_format", "text"),
            product_context=product_context,
            provider=provider,
            provider_keys=provider_keys,
            base_url=os.environ.get(
                "CD_AGENCY_BASE_URL",
                file_config.get("base_url", ""),
            ),
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
        if not self.api_key and self.provider != "ollama":
            errors.append(
                f"API key is not set for provider '{self.provider}'. "
                f"Set it via environment variable or config file."
            )
        if not self.agents_dir.exists():
            errors.append(f"Agents directory not found: {self.agents_dir}")
        return errors
