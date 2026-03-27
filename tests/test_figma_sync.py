"""Tests for Figma design system sync."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.design_system import ComponentConstraint, DesignSystem
from runtime.figma_sync import (
    FigmaClient,
    FigmaDesignSync,
    FigmaSyncConfig,
    FigmaToken,
    FigmaTokenExtractor,
    SyncState,
    _slugify,
    tokens_to_design_system,
)


# ---------------------------------------------------------------------------
# FigmaSyncConfig
# ---------------------------------------------------------------------------


class TestFigmaSyncConfig:
    def test_defaults(self):
        cfg = FigmaSyncConfig()
        assert cfg.file_key == ""
        assert cfg.access_token == ""
        assert cfg.sync_interval_minutes == 60
        assert cfg.auto_sync is False
        assert cfg.is_configured is False

    def test_is_configured(self):
        cfg = FigmaSyncConfig(file_key="abc", access_token="tok")
        assert cfg.is_configured is True

    def test_from_env(self):
        with patch.dict("os.environ", {
            "FIGMA_ACCESS_TOKEN": "my-token",
            "FIGMA_FILE_KEY": "my-key",
            "FIGMA_TEAM_ID": "team-1",
        }):
            cfg = FigmaSyncConfig.from_config()
            assert cfg.access_token == "my-token"
            assert cfg.file_key == "my-key"
            assert cfg.team_id == "team-1"

    def test_from_yaml(self, tmp_path):
        import yaml

        config_data = {
            "figma": {
                "file_key": "yaml-key",
                "access_token": "yaml-token",
                "sync_interval_minutes": 30,
                "auto_sync": True,
                "component_filter": ["Button", "Dialog"],
            }
        }
        (tmp_path / ".cd-agency.yaml").write_text(
            yaml.dump(config_data), encoding="utf-8"
        )

        with patch.dict("os.environ", {}, clear=True):
            cfg = FigmaSyncConfig.from_config(project_dir=tmp_path)

        assert cfg.file_key == "yaml-key"
        assert cfg.access_token == "yaml-token"
        assert cfg.sync_interval_minutes == 30
        assert cfg.auto_sync is True
        assert cfg.component_filter == ["Button", "Dialog"]

    def test_from_config_no_file(self, tmp_path):
        with patch.dict("os.environ", {}, clear=True):
            cfg = FigmaSyncConfig.from_config(project_dir=tmp_path)
        assert cfg.file_key == ""


# ---------------------------------------------------------------------------
# FigmaToken
# ---------------------------------------------------------------------------


class TestFigmaToken:
    def test_defaults(self):
        t = FigmaToken(name="test", value="val", token_type="variable")
        assert t.name == "test"
        assert t.collection == ""
        assert t.mode == ""


# ---------------------------------------------------------------------------
# FigmaTokenExtractor
# ---------------------------------------------------------------------------


class TestFigmaTokenExtractor:
    def test_extract_text_styles(self):
        extractor = FigmaTokenExtractor()
        response = {
            "meta": {
                "styles": [
                    {"name": "Heading/H1", "style_type": "TEXT", "key": "k1", "description": "Main heading"},
                    {"name": "Body", "style_type": "TEXT", "key": "k2", "description": ""},
                    {"name": "Primary", "style_type": "FILL", "key": "k3"},  # not text
                ],
            }
        }
        tokens = extractor.extract_text_styles(response)
        assert len(tokens) == 2
        assert tokens[0].name == "Heading/H1"
        assert tokens[0].token_type == "text-style"

    def test_extract_text_styles_empty(self):
        extractor = FigmaTokenExtractor()
        tokens = extractor.extract_text_styles({"meta": {"styles": []}})
        assert tokens == []

    def test_extract_variables(self):
        extractor = FigmaTokenExtractor()
        response = {
            "meta": {
                "variables": {
                    "v1": {
                        "name": "cta/primary",
                        "resolvedType": "STRING",
                        "variableCollectionId": "c1",
                        "valuesByMode": {"mode1": "Get started"},
                        "description": "Primary CTA label",
                    },
                    "v2": {
                        "name": "spacing/sm",
                        "resolvedType": "FLOAT",
                        "variableCollectionId": "c2",
                        "valuesByMode": {"mode1": 8},
                    },
                },
                "variableCollections": {
                    "c1": {"name": "Content"},
                    "c2": {"name": "Spacing"},
                },
            }
        }
        tokens = extractor.extract_variables(response)
        # Only STRING variables
        assert len(tokens) == 1
        assert tokens[0].name == "cta/primary"
        assert tokens[0].value == "Get started"
        assert tokens[0].collection == "Content"

    def test_extract_variables_empty(self):
        extractor = FigmaTokenExtractor()
        tokens = extractor.extract_variables({"meta": {"variables": {}, "variableCollections": {}}})
        assert tokens == []

    def test_extract_components(self):
        extractor = FigmaTokenExtractor()
        file_data = {
            "components": {
                "c1": {"name": "PrimaryButton", "description": "Max 25 characters"},
                "c2": {"name": "DialogTitle", "description": ""},
                "c3": {"name": "Icon/Star", "description": ""},
            }
        }
        tokens = extractor.extract_components(file_data)
        assert len(tokens) == 3

        button = next(t for t in tokens if t.name == "PrimaryButton")
        assert button.value["element"] == "button"
        assert button.value["char_limit"] == 25

        dialog = next(t for t in tokens if t.name == "DialogTitle")
        assert dialog.value["element"] == "modal_headline"

    def test_extract_components_with_filter(self):
        extractor = FigmaTokenExtractor()
        file_data = {
            "components": {
                "c1": {"name": "PrimaryButton", "description": ""},
                "c2": {"name": "DialogTitle", "description": ""},
                "c3": {"name": "Icon/Star", "description": ""},
            }
        }
        tokens = extractor.extract_components(file_data, component_filter=["Button"])
        assert len(tokens) == 1
        assert tokens[0].name == "PrimaryButton"

    def test_infer_element_type(self):
        extractor = FigmaTokenExtractor()
        assert extractor._infer_element_type("PrimaryButton") == "button"
        assert extractor._infer_element_type("SmallCTA") == "button"
        assert extractor._infer_element_type("TooltipContent") == "tooltip"
        assert extractor._infer_element_type("ErrorMessage") == "error_message"
        assert extractor._infer_element_type("RandomWidget") == "other"

    def test_parse_char_limit(self):
        extractor = FigmaTokenExtractor()
        assert extractor._parse_char_limit("Max 25 characters") == 25
        assert extractor._parse_char_limit("40 chars max") == 40
        assert extractor._parse_char_limit("limit: 60 characters") == 60
        assert extractor._parse_char_limit("max length: 30") == 30
        assert extractor._parse_char_limit("No limit info here") == 0
        assert extractor._parse_char_limit("") == 0


# ---------------------------------------------------------------------------
# tokens_to_design_system
# ---------------------------------------------------------------------------


class TestTokensToDesignSystem:
    def test_empty_tokens(self):
        ds = tokens_to_design_system([])
        assert ds.name == "Figma Design System"
        assert ds.components == []

    def test_component_tokens(self):
        tokens = [
            FigmaToken(
                name="PrimaryButton",
                value={"element": "button", "char_limit": 25, "description": "CTA"},
                token_type="component",
                description="CTA button",
            ),
            FigmaToken(
                name="DialogTitle",
                value={"element": "modal_headline", "char_limit": 50, "description": ""},
                token_type="component",
            ),
        ]
        ds = tokens_to_design_system(tokens, name="Test DS")
        assert ds.name == "Test DS"
        assert len(ds.components) == 2
        assert ds.components[0].component == "PrimaryButton"
        assert ds.components[0].max_chars == 25
        assert ds.components[0].element == "button"

    def test_variable_tokens(self):
        tokens = [
            FigmaToken(name="cta/sign_in", value="Sign in", token_type="variable"),
            FigmaToken(name="label/cancel", value="Cancel", token_type="variable"),
        ]
        ds = tokens_to_design_system(tokens)
        assert "cta_sign_in" in ds.terminology
        assert ds.terminology["cta_sign_in"] == "Sign in"

    def test_merge_with_existing(self):
        existing = DesignSystem(
            name="Base DS",
            components=[
                ComponentConstraint(component="OldButton", element="button", max_chars=20),
            ],
            terminology={"sign_in": "Sign in"},
            voice_principles=["Be concise"],
        )
        tokens = [
            FigmaToken(
                name="NewTooltip",
                value={"element": "tooltip", "char_limit": 60, "description": ""},
                token_type="component",
            ),
        ]
        ds = tokens_to_design_system(tokens, existing=existing)
        assert ds.name == "Base DS"
        assert len(ds.components) == 2
        assert ds.terminology["sign_in"] == "Sign in"
        assert ds.voice_principles == ["Be concise"]

    def test_merge_updates_existing_component(self):
        existing = DesignSystem(
            name="DS",
            components=[
                ComponentConstraint(component="Button", element="button", max_chars=20),
            ],
        )
        tokens = [
            FigmaToken(
                name="Button",
                value={"element": "button", "char_limit": 30, "description": ""},
                token_type="component",
            ),
        ]
        ds = tokens_to_design_system(tokens, existing=existing)
        assert len(ds.components) == 1
        assert ds.components[0].max_chars == 30

    def test_skips_component_no_info(self):
        tokens = [
            FigmaToken(
                name="Unknown",
                value={"element": "other", "char_limit": 0, "description": ""},
                token_type="component",
            ),
        ]
        ds = tokens_to_design_system(tokens)
        assert len(ds.components) == 0


# ---------------------------------------------------------------------------
# SyncState
# ---------------------------------------------------------------------------


class TestSyncState:
    def test_defaults(self):
        state = SyncState()
        assert state.last_sync_timestamp == 0.0
        assert state.is_stale(60) is True

    def test_not_stale(self):
        state = SyncState(last_sync_timestamp=time.time())
        assert state.is_stale(60) is False

    def test_stale_after_interval(self):
        state = SyncState(last_sync_timestamp=time.time() - 3700)
        assert state.is_stale(60) is True

    def test_save_and_load(self, tmp_path):
        path = tmp_path / ".cd-agency" / "figma_cache.json"
        state = SyncState(
            last_sync_timestamp=1000.0,
            file_key="abc",
            file_name="My File",
            token_count=10,
            component_count=5,
            variable_count=3,
            design_system_snapshot={"name": "Test"},
        )
        state.save(path)

        loaded = SyncState.load(path)
        assert loaded.last_sync_timestamp == 1000.0
        assert loaded.file_key == "abc"
        assert loaded.file_name == "My File"
        assert loaded.design_system_snapshot == {"name": "Test"}

    def test_load_missing(self, tmp_path):
        state = SyncState.load(tmp_path / "nonexistent.json")
        assert state.last_sync_timestamp == 0.0

    def test_load_corrupt(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json", encoding="utf-8")
        state = SyncState.load(path)
        assert state.last_sync_timestamp == 0.0


# ---------------------------------------------------------------------------
# _slugify
# ---------------------------------------------------------------------------


class TestSlugify:
    def test_simple(self):
        assert _slugify("Sign In") == "sign_in"
        assert _slugify("cta/primary") == "cta_primary"
        assert _slugify("Hello World!") == "hello_world"
        assert _slugify("UPPER_CASE") == "upper_case"


# ---------------------------------------------------------------------------
# FigmaDesignSync
# ---------------------------------------------------------------------------


class TestFigmaDesignSync:
    def test_not_configured(self, tmp_path):
        cfg = FigmaSyncConfig()
        sync = FigmaDesignSync(cfg, project_dir=tmp_path)
        assert sync.is_configured is False

        with pytest.raises(RuntimeError, match="not configured"):
            sync.sync()

    def test_get_cached_empty(self, tmp_path):
        cfg = FigmaSyncConfig(file_key="k", access_token="t")
        sync = FigmaDesignSync(cfg, project_dir=tmp_path)
        assert sync.get_cached() is None

    def test_get_cached_with_data(self, tmp_path):
        # Write a cache file
        cache_path = tmp_path / ".cd-agency" / "figma_cache.json"
        cache_path.parent.mkdir(parents=True)
        state = SyncState(
            last_sync_timestamp=time.time(),
            file_key="k",
            design_system_snapshot={
                "name": "Cached DS",
                "components": [
                    {"component": "Btn", "element": "button", "max_chars": 20,
                     "min_chars": 0, "max_lines": 0, "notes": "", "platform_overrides": {}},
                ],
                "terminology": {"sign_in": "Sign in"},
                "voice_principles": ["Be clear"],
            },
        )
        state.save(cache_path)

        cfg = FigmaSyncConfig(file_key="k", access_token="t")
        sync = FigmaDesignSync(cfg, project_dir=tmp_path)
        ds = sync.get_cached()

        assert ds is not None
        assert ds.name == "Cached DS"
        assert len(ds.components) == 1
        assert ds.terminology["sign_in"] == "Sign in"

    def test_get_sync_status(self, tmp_path):
        cfg = FigmaSyncConfig(file_key="k", access_token="t", auto_sync=True)
        sync = FigmaDesignSync(cfg, project_dir=tmp_path)
        status = sync.get_sync_status()

        assert status["configured"] is True
        assert status["auto_sync"] is True
        assert status["is_stale"] is True
        assert status["last_sync"] == 0

    def test_clear_cache(self, tmp_path):
        cache_path = tmp_path / ".cd-agency" / "figma_cache.json"
        cache_path.parent.mkdir(parents=True)
        cache_path.write_text("{}", encoding="utf-8")

        cfg = FigmaSyncConfig(file_key="k", access_token="t")
        sync = FigmaDesignSync(cfg, project_dir=tmp_path)
        sync.clear_cache()
        assert not cache_path.exists()

    def test_sync_uses_cache_when_fresh(self, tmp_path):
        cache_path = tmp_path / ".cd-agency" / "figma_cache.json"
        cache_path.parent.mkdir(parents=True)
        state = SyncState(
            last_sync_timestamp=time.time(),
            file_key="k",
            design_system_snapshot={"name": "Fresh DS"},
        )
        state.save(cache_path)

        cfg = FigmaSyncConfig(file_key="k", access_token="t")
        sync = FigmaDesignSync(cfg, project_dir=tmp_path)
        # Should not call the API, just return from cache
        ds = sync.sync()
        assert ds.name == "Fresh DS"

    @patch("runtime.figma_sync.FigmaClient")
    def test_sync_calls_api_when_stale(self, MockClient, tmp_path):
        client = MockClient.return_value
        client.get_file.return_value = {
            "name": "My Figma File",
            "components": {
                "c1": {"name": "PrimaryButton", "description": "25 chars max"},
            },
        }
        client.get_file_styles.return_value = {"meta": {"styles": []}}
        client.get_file_variables.return_value = {
            "meta": {"variables": {}, "variableCollections": {}}
        }

        cfg = FigmaSyncConfig(file_key="k", access_token="t")
        sync = FigmaDesignSync(cfg, project_dir=tmp_path)
        sync._client = client

        ds = sync._do_sync(SyncState())

        assert ds.name == "My Figma File (Figma)"
        assert len(ds.components) == 1
        assert ds.components[0].max_chars == 25
        client.get_file.assert_called_once_with("k")

    @patch("runtime.figma_sync.FigmaClient")
    def test_sync_handles_api_errors_gracefully(self, MockClient, tmp_path):
        client = MockClient.return_value
        client.get_file.return_value = {
            "name": "File",
            "components": {},
        }
        client.get_file_styles.side_effect = Exception("API error")
        client.get_file_variables.side_effect = Exception("API error")

        cfg = FigmaSyncConfig(file_key="k", access_token="t")
        sync = FigmaDesignSync(cfg, project_dir=tmp_path)
        sync._client = client

        # Should not raise despite API errors on styles/variables
        ds = sync._do_sync(SyncState())
        assert ds.name == "File (Figma)"

    def test_from_config(self, tmp_path):
        with patch.dict("os.environ", {"FIGMA_ACCESS_TOKEN": "t", "FIGMA_FILE_KEY": "k"}):
            sync = FigmaDesignSync.from_config(project_dir=tmp_path)
        assert sync.is_configured is True


# ---------------------------------------------------------------------------
# FigmaClient (unit tests with mocked urllib)
# ---------------------------------------------------------------------------


class TestFigmaClient:
    @patch("urllib.request.urlopen")
    def test_request_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"ok": True}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        client = FigmaClient("my-token")
        result = client._request("files/abc")
        assert result == {"ok": True}

    @patch("urllib.request.urlopen")
    def test_request_failure(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Network error")

        client = FigmaClient("my-token")
        with pytest.raises(Exception, match="Network error"):
            client._request("files/abc")
