"""Tests for the design system integration module."""

import pytest
from pathlib import Path

from runtime.design_system import (
    ComponentConstraint,
    DesignSystem,
    load_design_system,
    load_design_system_from_config,
)


@pytest.fixture
def sample_constraint() -> ComponentConstraint:
    return ComponentConstraint(
        component="PrimaryButton",
        element="button",
        max_chars=20,
        min_chars=2,
        max_lines=1,
        notes="Single action verb",
        platform_overrides={"ios": 18, "android": 22},
    )


@pytest.fixture
def sample_design_system(sample_constraint: ComponentConstraint) -> DesignSystem:
    return DesignSystem(
        name="Test Design System",
        version="2.0",
        description="Test constraints",
        default_platform="web",
        capitalization="sentence",
        components=[
            sample_constraint,
            ComponentConstraint(
                component="DialogTitle",
                element="modal_headline",
                max_chars=50,
            ),
        ],
        terminology={"Save": "Submit", "Settings": "Preferences"},
        voice_principles=["Be concise", "Use active voice"],
    )


class TestComponentConstraint:
    def test_get_limit_default(self, sample_constraint: ComponentConstraint):
        assert sample_constraint.get_limit() == 20

    def test_get_limit_platform_override(self, sample_constraint: ComponentConstraint):
        assert sample_constraint.get_limit("ios") == 18
        assert sample_constraint.get_limit("android") == 22

    def test_get_limit_unknown_platform(self, sample_constraint: ComponentConstraint):
        assert sample_constraint.get_limit("web") == 20

    def test_get_limit_none_platform(self, sample_constraint: ComponentConstraint):
        assert sample_constraint.get_limit(None) == 20


class TestDesignSystem:
    def test_get_component_found(self, sample_design_system: DesignSystem):
        comp = sample_design_system.get_component("PrimaryButton")
        assert comp is not None
        assert comp.max_chars == 20

    def test_get_component_not_found(self, sample_design_system: DesignSystem):
        assert sample_design_system.get_component("NonExistent") is None

    def test_get_components_by_element(self, sample_design_system: DesignSystem):
        comps = sample_design_system.get_components_by_element("button")
        assert len(comps) == 1
        assert comps[0].component == "PrimaryButton"

    def test_get_components_by_element_empty(self, sample_design_system: DesignSystem):
        comps = sample_design_system.get_components_by_element("nonexistent")
        assert len(comps) == 0

    def test_build_context_block(self, sample_design_system: DesignSystem):
        block = sample_design_system.build_context_block()
        assert "Test Design System" in block
        assert "sentence case" in block
        assert "PrimaryButton" in block
        assert "20 chars max" in block
        assert "1 lines max" in block
        assert "Single action verb" in block
        assert "DialogTitle" in block
        assert '"Save"' in block
        assert '"Submit"' in block
        assert "Be concise" in block
        assert "Use active voice" in block
        assert "Apply these design system constraints" in block

    def test_build_context_block_minimal(self):
        ds = DesignSystem(name="Minimal")
        block = ds.build_context_block()
        assert "Minimal" in block
        assert "Component Constraints" not in block
        assert "Terminology" not in block

    def test_to_dict(self, sample_design_system: DesignSystem):
        d = sample_design_system.to_dict()
        assert d["name"] == "Test Design System"
        assert d["version"] == "2.0"
        assert len(d["components"]) == 2
        assert d["components"][0]["component"] == "PrimaryButton"
        assert d["components"][0]["max_chars"] == 20
        assert d["terminology"]["Save"] == "Submit"
        assert len(d["voice_principles"]) == 2


class TestLoadDesignSystem:
    def test_load_from_yaml(self, tmp_path: Path):
        yaml_content = """
name: "My DS"
version: "1.0"
description: "Test"
default_platform: web
capitalization: sentence

components:
  - component: Button
    element: button
    max_chars: 25
    notes: "Keep it short"
  - component: Title
    element: modal_headline
    max_chars: 50
    max_lines: 2

terminology:
  Save: Submit
  Settings: Preferences

voice_principles:
  - "Be concise"
  - "Use active voice"
"""
        filepath = tmp_path / "design-system.yaml"
        filepath.write_text(yaml_content, encoding="utf-8")

        ds = load_design_system(filepath)
        assert ds.name == "My DS"
        assert ds.version == "1.0"
        assert len(ds.components) == 2
        assert ds.components[0].component == "Button"
        assert ds.components[0].max_chars == 25
        assert ds.components[1].max_lines == 2
        assert ds.terminology["Save"] == "Submit"
        assert len(ds.voice_principles) == 2

    def test_load_minimal_yaml(self, tmp_path: Path):
        filepath = tmp_path / "minimal.yaml"
        filepath.write_text("name: Minimal\n", encoding="utf-8")

        ds = load_design_system(filepath)
        assert ds.name == "Minimal"
        assert ds.components == []
        assert ds.terminology == {}

    def test_load_uses_filename_as_name(self, tmp_path: Path):
        filepath = tmp_path / "my-system.yaml"
        filepath.write_text("{}\n", encoding="utf-8")

        ds = load_design_system(filepath)
        assert ds.name == "my-system"

    def test_load_with_platform_overrides(self, tmp_path: Path):
        yaml_content = """
name: "Override Test"
components:
  - component: Button
    element: button
    max_chars: 25
    platform_overrides:
      ios: 20
      android: 28
"""
        filepath = tmp_path / "overrides.yaml"
        filepath.write_text(yaml_content, encoding="utf-8")

        ds = load_design_system(filepath)
        btn = ds.components[0]
        assert btn.get_limit() == 25
        assert btn.get_limit("ios") == 20
        assert btn.get_limit("android") == 28


class TestLoadDesignSystemFromConfig:
    def test_no_config_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(tmp_path)
        result = load_design_system_from_config()
        assert result is None

    def test_config_without_design_system(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".cd-agency.yaml").write_text("model: claude-3\n", encoding="utf-8")
        result = load_design_system_from_config()
        assert result is None

    def test_config_with_design_system(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(tmp_path)

        # Create design system file
        ds_path = tmp_path / "design-system.yaml"
        ds_path.write_text("name: FromConfig\nversion: '1.0'\n", encoding="utf-8")

        # Create config pointing to it
        config_path = tmp_path / ".cd-agency.yaml"
        config_path.write_text(f"design_system: {ds_path}\n", encoding="utf-8")

        result = load_design_system_from_config()
        assert result is not None
        assert result.name == "FromConfig"

    def test_config_with_missing_design_system_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(tmp_path)
        config_path = tmp_path / ".cd-agency.yaml"
        config_path.write_text("design_system: nonexistent.yaml\n", encoding="utf-8")
        result = load_design_system_from_config()
        assert result is None
