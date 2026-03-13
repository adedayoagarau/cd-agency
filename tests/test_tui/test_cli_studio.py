"""Tests for the studio CLI command."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from runtime.cli import main


class TestStudioCommand:
    """Tests for the cd-agency studio command."""

    def test_studio_command_exists(self):
        """The studio command should be registered."""
        runner = CliRunner()
        result = runner.invoke(main, ["studio", "--help"])
        assert result.exit_code == 0
        assert "Launch the interactive studio" in result.output

    def test_studio_help_shows_shortcuts(self):
        """Help should mention keyboard shortcuts."""
        runner = CliRunner()
        result = runner.invoke(main, ["studio", "--help"])
        assert "Ctrl+P" in result.output
        assert "Ctrl+T" in result.output

    def test_studio_preset_option(self):
        """Studio should accept --preset option."""
        runner = CliRunner()
        result = runner.invoke(main, ["studio", "--help"])
        assert "--preset" in result.output

    def test_studio_content_option(self):
        """Studio should accept --content option."""
        runner = CliRunner()
        result = runner.invoke(main, ["studio", "--help"])
        assert "--content" in result.output

    def test_studio_file_option(self):
        """Studio should accept --file option."""
        runner = CliRunner()
        result = runner.invoke(main, ["studio", "--help"])
        assert "--file" in result.output
