"""Live design system sync from Figma.

Fetches design tokens (text styles, variables, component constraints) from a
Figma file via the Figma REST API and converts them into a DesignSystem that
agents can use for content validation.

Requires a Figma personal access token (FIGMA_ACCESS_TOKEN env var or config).
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runtime.design_system import ComponentConstraint, DesignSystem

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class FigmaToken:
    """A single design token extracted from Figma."""

    name: str
    value: Any
    token_type: str  # "text-style", "variable", "component"
    collection: str = ""
    mode: str = ""
    description: str = ""


@dataclass
class FigmaSyncConfig:
    """Configuration for Figma design system sync."""

    file_key: str = ""
    access_token: str = ""
    team_id: str = ""
    sync_interval_minutes: int = 60
    auto_sync: bool = False
    token_mapping: dict[str, str] = field(default_factory=dict)
    component_filter: list[str] = field(default_factory=list)
    cache_path: str = ".cd-agency/figma_cache.json"

    @classmethod
    def from_config(cls, project_dir: Path | None = None) -> FigmaSyncConfig:
        """Load config from .cd-agency.yaml or environment."""
        import os

        config = cls()
        config.access_token = os.environ.get("FIGMA_ACCESS_TOKEN", "")
        config.file_key = os.environ.get("FIGMA_FILE_KEY", "")
        config.team_id = os.environ.get("FIGMA_TEAM_ID", "")

        # Try loading from project config
        search_dirs = [project_dir] if project_dir else [Path.cwd()]
        for base in search_dirs:
            if base is None:
                continue
            for name in (".cd-agency.yaml", ".cd-agency.yml"):
                cfg_path = base / name
                if cfg_path.exists():
                    try:
                        import yaml

                        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
                        figma = data.get("figma", {})
                        if figma:
                            config.file_key = figma.get("file_key", config.file_key)
                            config.access_token = figma.get("access_token", config.access_token)
                            config.team_id = figma.get("team_id", config.team_id)
                            config.sync_interval_minutes = figma.get(
                                "sync_interval_minutes", config.sync_interval_minutes
                            )
                            config.auto_sync = figma.get("auto_sync", config.auto_sync)
                            config.token_mapping = figma.get("token_mapping", {})
                            config.component_filter = figma.get("component_filter", [])
                    except Exception:
                        pass
                    break

        return config

    @property
    def is_configured(self) -> bool:
        """Check if minimum config is present for API calls."""
        return bool(self.file_key and self.access_token)


# ---------------------------------------------------------------------------
# Figma API client (minimal, no external deps beyond stdlib)
# ---------------------------------------------------------------------------


class FigmaClient:
    """Minimal Figma REST API client using urllib."""

    BASE_URL = "https://api.figma.com/v1"

    def __init__(self, access_token: str) -> None:
        self._token = access_token

    def _request(self, endpoint: str) -> dict[str, Any]:
        """Make an authenticated GET request to the Figma API."""
        import urllib.request

        url = f"{self.BASE_URL}/{endpoint}"
        req = urllib.request.Request(url)
        req.add_header("X-Figma-Token", self._token)
        req.add_header("Accept", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            _logger.warning("Figma API request failed: %s — %s", endpoint, exc)
            raise

    def get_file(self, file_key: str) -> dict[str, Any]:
        """Get a Figma file's document tree."""
        return self._request(f"files/{file_key}")

    def get_file_styles(self, file_key: str) -> dict[str, Any]:
        """Get published styles from a Figma file."""
        return self._request(f"files/{file_key}/styles")

    def get_file_variables(self, file_key: str) -> dict[str, Any]:
        """Get local variables from a Figma file."""
        return self._request(f"files/{file_key}/variables/local")

    def get_team_styles(self, team_id: str) -> dict[str, Any]:
        """Get published styles for a team."""
        return self._request(f"teams/{team_id}/styles")

    def get_file_nodes(self, file_key: str, node_ids: list[str]) -> dict[str, Any]:
        """Get specific nodes from a Figma file."""
        ids = ",".join(node_ids)
        return self._request(f"files/{file_key}/nodes?ids={ids}")


# ---------------------------------------------------------------------------
# Token extractor
# ---------------------------------------------------------------------------


class FigmaTokenExtractor:
    """Extracts content-relevant design tokens from Figma API responses."""

    # Common component name patterns → element type mapping
    COMPONENT_ELEMENT_MAP: dict[str, str] = {
        "button": "button",
        "btn": "button",
        "cta": "button",
        "dialog": "modal_headline",
        "modal": "modal_headline",
        "tooltip": "tooltip",
        "toast": "snackbar",
        "snackbar": "snackbar",
        "notification": "notification_body",
        "alert": "snackbar",
        "badge": "badge",
        "chip": "badge",
        "tab": "button",
        "menu": "menu_item",
        "label": "label",
        "heading": "heading",
        "title": "heading",
        "subtitle": "subheading",
        "body": "body",
        "caption": "caption",
        "helper": "helper_text",
        "error": "error_message",
        "placeholder": "placeholder",
        "input": "input_label",
    }

    def extract_text_styles(self, styles_response: dict[str, Any]) -> list[FigmaToken]:
        """Extract text styles from Figma styles response."""
        tokens: list[FigmaToken] = []
        meta = styles_response.get("meta", {})
        styles = meta.get("styles", [])

        for style in styles:
            if style.get("style_type") != "TEXT":
                continue
            tokens.append(FigmaToken(
                name=style.get("name", ""),
                value={
                    "key": style.get("key", ""),
                    "description": style.get("description", ""),
                },
                token_type="text-style",
                description=style.get("description", ""),
            ))

        return tokens

    def extract_variables(self, variables_response: dict[str, Any]) -> list[FigmaToken]:
        """Extract variables from Figma variables response."""
        tokens: list[FigmaToken] = []
        meta = variables_response.get("meta", {})
        variables = meta.get("variables", {})
        collections = meta.get("variableCollections", {})

        # Build collection name lookup
        collection_names: dict[str, str] = {}
        for cid, coll in collections.items():
            collection_names[cid] = coll.get("name", cid)

        for vid, var in variables.items():
            name = var.get("name", vid)
            resolved_type = var.get("resolvedType", "")

            # We care about STRING variables (content tokens)
            if resolved_type != "STRING":
                continue

            coll_id = var.get("variableCollectionId", "")
            values_by_mode = var.get("valuesByMode", {})

            for mode_id, value in values_by_mode.items():
                tokens.append(FigmaToken(
                    name=name,
                    value=value,
                    token_type="variable",
                    collection=collection_names.get(coll_id, ""),
                    mode=mode_id,
                    description=var.get("description", ""),
                ))

        return tokens

    def extract_components(
        self, file_data: dict[str, Any], component_filter: list[str] | None = None
    ) -> list[FigmaToken]:
        """Extract component constraints from Figma file document tree."""
        tokens: list[FigmaToken] = []
        components = file_data.get("components", {})

        for comp_id, comp in components.items():
            name = comp.get("name", "")
            description = comp.get("description", "")

            if component_filter and not any(
                f.lower() in name.lower() for f in component_filter
            ):
                continue

            # Try to infer element type from component name
            element = self._infer_element_type(name)

            # Parse character limits from description if present
            char_limit = self._parse_char_limit(description)

            tokens.append(FigmaToken(
                name=name,
                value={
                    "id": comp_id,
                    "element": element,
                    "char_limit": char_limit,
                    "description": description,
                },
                token_type="component",
                description=description,
            ))

        return tokens

    def _infer_element_type(self, component_name: str) -> str:
        """Infer the element type from a component name."""
        name_lower = component_name.lower()
        for pattern, element in self.COMPONENT_ELEMENT_MAP.items():
            if pattern in name_lower:
                return element
        return "other"

    def _parse_char_limit(self, description: str) -> int:
        """Try to extract a character limit from a component description."""
        if not description:
            return 0

        patterns = [
            r"(\d+)\s*char(?:acter)?s?\s*(?:max|limit)",
            r"max\s*(?:length|chars?|characters?)[\s:]*(\d+)",
            r"max\s+(\d+)\s*char",
            r"limit[\s:]*(\d+)\s*char",
        ]
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return 0


# ---------------------------------------------------------------------------
# Design system builder
# ---------------------------------------------------------------------------


def tokens_to_design_system(
    tokens: list[FigmaToken],
    name: str = "Figma Design System",
    existing: DesignSystem | None = None,
) -> DesignSystem:
    """Convert extracted Figma tokens into a DesignSystem.

    If *existing* is provided, merges Figma tokens into it (Figma wins on
    conflicts for component constraints but preserves existing terminology
    and voice principles).
    """
    components: list[ComponentConstraint] = []
    terminology: dict[str, str] = {}
    voice_principles: list[str] = []

    if existing:
        components = list(existing.components)
        terminology = dict(existing.terminology)
        voice_principles = list(existing.voice_principles)
        name = existing.name

    seen_components: set[str] = {c.component for c in components}

    for token in tokens:
        if token.token_type == "component":
            comp_name = token.name
            val = token.value if isinstance(token.value, dict) else {}
            element = val.get("element", "other")
            char_limit = val.get("char_limit", 0)

            if comp_name in seen_components:
                # Update existing constraint
                for c in components:
                    if c.component == comp_name:
                        if char_limit:
                            c.max_chars = char_limit
                        if element != "other":
                            c.element = element
                        break
            elif char_limit > 0 or element != "other":
                components.append(ComponentConstraint(
                    component=comp_name,
                    element=element,
                    max_chars=char_limit or 100,
                    notes=token.description,
                ))
                seen_components.add(comp_name)

        elif token.token_type == "variable":
            # String variables can represent terminology mappings
            if isinstance(token.value, str) and token.value:
                key = _slugify(token.name)
                terminology[key] = token.value

    return DesignSystem(
        name=name,
        components=components,
        terminology=terminology,
        voice_principles=voice_principles,
    )


def _slugify(name: str) -> str:
    """Convert a Figma variable name to a terminology key."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# ---------------------------------------------------------------------------
# Sync cache
# ---------------------------------------------------------------------------


@dataclass
class SyncState:
    """Tracks the last successful sync."""

    last_sync_timestamp: float = 0.0
    file_key: str = ""
    file_name: str = ""
    token_count: int = 0
    component_count: int = 0
    variable_count: int = 0
    design_system_snapshot: dict[str, Any] = field(default_factory=dict)

    def is_stale(self, interval_minutes: int) -> bool:
        """Check if the cached data is older than the sync interval."""
        if self.last_sync_timestamp == 0:
            return True
        elapsed = time.time() - self.last_sync_timestamp
        return elapsed > (interval_minutes * 60)

    def save(self, path: Path) -> None:
        """Persist sync state to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "last_sync_timestamp": self.last_sync_timestamp,
            "file_key": self.file_key,
            "file_name": self.file_name,
            "token_count": self.token_count,
            "component_count": self.component_count,
            "variable_count": self.variable_count,
            "design_system_snapshot": self.design_system_snapshot,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> SyncState:
        """Load sync state from disk."""
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(
                last_sync_timestamp=data.get("last_sync_timestamp", 0.0),
                file_key=data.get("file_key", ""),
                file_name=data.get("file_name", ""),
                token_count=data.get("token_count", 0),
                component_count=data.get("component_count", 0),
                variable_count=data.get("variable_count", 0),
                design_system_snapshot=data.get("design_system_snapshot", {}),
            )
        except (json.JSONDecodeError, KeyError):
            return cls()


# ---------------------------------------------------------------------------
# Main sync orchestrator
# ---------------------------------------------------------------------------


class FigmaDesignSync:
    """Orchestrates syncing a Figma file into a local DesignSystem.

    Usage::

        sync = FigmaDesignSync.from_config()
        ds = sync.sync()         # full sync from Figma API
        ds = sync.get_cached()   # load from cache (no API call)
    """

    def __init__(
        self,
        config: FigmaSyncConfig,
        project_dir: Path | None = None,
    ) -> None:
        self._config = config
        self._project_dir = project_dir or Path.cwd()
        self._cache_path = self._project_dir / config.cache_path
        self._client: FigmaClient | None = None
        self._extractor = FigmaTokenExtractor()

    @classmethod
    def from_config(cls, project_dir: Path | None = None) -> FigmaDesignSync:
        """Create a sync instance from project config / env vars."""
        config = FigmaSyncConfig.from_config(project_dir)
        return cls(config, project_dir)

    @property
    def is_configured(self) -> bool:
        return self._config.is_configured

    def _get_client(self) -> FigmaClient:
        if self._client is None:
            self._client = FigmaClient(self._config.access_token)
        return self._client

    # -- Public API ---------------------------------------------------------

    def sync(self, force: bool = False) -> DesignSystem:
        """Sync design tokens from Figma and return a DesignSystem.

        Uses cache if available and not stale, unless *force* is True.
        Raises RuntimeError if Figma is not configured.
        """
        if not self._config.is_configured:
            raise RuntimeError(
                "Figma sync not configured. Set FIGMA_ACCESS_TOKEN and "
                "FIGMA_FILE_KEY, or add figma config to .cd-agency.yaml."
            )

        state = SyncState.load(self._cache_path)

        if not force and not state.is_stale(self._config.sync_interval_minutes):
            _logger.debug("Figma cache fresh, skipping sync")
            return self._ds_from_snapshot(state.design_system_snapshot)

        return self._do_sync(state)

    def get_cached(self) -> DesignSystem | None:
        """Return the cached design system without making API calls.

        Returns None if no cache exists.
        """
        state = SyncState.load(self._cache_path)
        if state.last_sync_timestamp == 0:
            return None
        return self._ds_from_snapshot(state.design_system_snapshot)

    def get_sync_status(self) -> dict[str, Any]:
        """Return current sync status for dashboard / CLI."""
        state = SyncState.load(self._cache_path)
        is_stale = state.is_stale(self._config.sync_interval_minutes)
        return {
            "configured": self._config.is_configured,
            "last_sync": state.last_sync_timestamp,
            "file_key": state.file_key,
            "file_name": state.file_name,
            "token_count": state.token_count,
            "component_count": state.component_count,
            "variable_count": state.variable_count,
            "is_stale": is_stale,
            "auto_sync": self._config.auto_sync,
            "interval_minutes": self._config.sync_interval_minutes,
        }

    def clear_cache(self) -> None:
        """Remove the sync cache file."""
        if self._cache_path.exists():
            self._cache_path.unlink()

    # -- Internal -----------------------------------------------------------

    def _do_sync(self, state: SyncState) -> DesignSystem:
        """Perform the actual sync from Figma API."""
        client = self._get_client()
        file_key = self._config.file_key
        all_tokens: list[FigmaToken] = []

        # 1. Fetch file metadata + components
        _logger.info("Syncing Figma file %s…", file_key)
        file_data = client.get_file(file_key)
        file_name = file_data.get("name", file_key)

        comp_tokens = self._extractor.extract_components(
            file_data, self._config.component_filter or None
        )
        all_tokens.extend(comp_tokens)

        # 2. Fetch text styles
        try:
            styles_data = client.get_file_styles(file_key)
            text_tokens = self._extractor.extract_text_styles(styles_data)
            all_tokens.extend(text_tokens)
        except Exception:
            _logger.debug("Could not fetch text styles, skipping")

        # 3. Fetch variables (string tokens)
        try:
            var_data = client.get_file_variables(file_key)
            var_tokens = self._extractor.extract_variables(var_data)
            all_tokens.extend(var_tokens)
        except Exception:
            _logger.debug("Could not fetch variables, skipping")

        # 4. Build design system, optionally merging with existing preset
        existing = self._load_existing_preset()
        ds = tokens_to_design_system(
            all_tokens,
            name=f"{file_name} (Figma)",
            existing=existing,
        )

        # 5. Update cache
        state.last_sync_timestamp = time.time()
        state.file_key = file_key
        state.file_name = file_name
        state.token_count = len(all_tokens)
        state.component_count = len(comp_tokens)
        state.variable_count = len([t for t in all_tokens if t.token_type == "variable"])
        state.design_system_snapshot = ds.to_dict()
        state.save(self._cache_path)

        _logger.info(
            "Figma sync complete: %d tokens (%d components, %d variables)",
            len(all_tokens),
            state.component_count,
            state.variable_count,
        )
        return ds

    def _load_existing_preset(self) -> DesignSystem | None:
        """Load an existing preset to merge Figma data into."""
        from runtime.design_system import load_design_system_from_config

        return load_design_system_from_config()

    def _ds_from_snapshot(self, snapshot: dict[str, Any]) -> DesignSystem:
        """Reconstruct a DesignSystem from a cached snapshot dict."""
        if not snapshot:
            return DesignSystem(name="(empty)")

        components = [
            ComponentConstraint(
                component=c.get("component", ""),
                element=c.get("element", ""),
                max_chars=c.get("max_chars", 0),
                min_chars=c.get("min_chars", 0),
                max_lines=c.get("max_lines", 0),
                notes=c.get("notes", ""),
                platform_overrides=c.get("platform_overrides", {}),
            )
            for c in snapshot.get("components", [])
        ]

        return DesignSystem(
            name=snapshot.get("name", "Figma Design System"),
            version=snapshot.get("version", ""),
            description=snapshot.get("description", ""),
            default_platform=snapshot.get("default_platform", "web"),
            capitalization=snapshot.get("capitalization", "sentence"),
            components=components,
            terminology=snapshot.get("terminology", {}),
            voice_principles=snapshot.get("voice_principles", []),
        )
