"""Scoring dashboard — live readability, lint, and accessibility scores."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from tools.scoring import ReadabilityScorer
from tools.linter import ContentLinter
from tools.a11y_checker import A11yChecker


class ScoringPanel(Widget):
    """Right sidebar showing live content quality scores."""

    DEFAULT_CSS = """
    ScoringPanel {
        width: 30;
        dock: right;
        background: $surface;
        border-left: solid $primary-background;
        padding: 1;
    }
    ScoringPanel .score-title {
        text-style: bold;
        color: $text;
        padding: 0 0 1 0;
    }
    ScoringPanel .score-section {
        padding: 0 0 1 0;
    }
    ScoringPanel .score-heading {
        text-style: bold;
        color: $accent;
    }
    ScoringPanel .score-good {
        color: $success;
    }
    ScoringPanel .score-warn {
        color: $warning;
    }
    ScoringPanel .score-bad {
        color: $error;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._scorer = ReadabilityScorer()
        self._linter = ContentLinter()
        self._a11y = A11yChecker()

    def compose(self) -> ComposeResult:
        yield Static("SCORING", classes="score-title")
        yield Static("", id="readability-score", classes="score-section")
        yield Static("", id="lint-score", classes="score-section")
        yield Static("", id="a11y-score", classes="score-section")
        yield Static("[dim]Type or score content to see results[/dim]", id="score-hint")

    def update_scores(self, text: str) -> None:
        """Recalculate and display all scores for the given text."""
        if not text.strip():
            self.query_one("#readability-score", Static).update("")
            self.query_one("#lint-score", Static).update("")
            self.query_one("#a11y-score", Static).update("")
            self.query_one("#score-hint", Static).update(
                "[dim]Type or score content to see results[/dim]"
            )
            return

        self.query_one("#score-hint", Static).update("")

        # Readability
        result = self._scorer.score(text)
        ease_color = "score-good" if result.flesch_reading_ease >= 60 else (
            "score-warn" if result.flesch_reading_ease >= 30 else "score-bad"
        )
        self.query_one("#readability-score", Static).update(
            f"[bold]Readability[/bold]\n"
            f"  Flesch: [{ease_color}]{result.flesch_reading_ease:.1f}[/{ease_color}]\n"
            f"  Grade: {result.grade_label}\n"
            f"  Words: {result.word_count}\n"
            f"  Chars: {result.character_count}"
        )

        # Lint
        lint_results = self._linter.lint(text)
        failures = [r for r in lint_results if not r.passed]
        errors = [r for r in failures if r.severity.value == "error"]
        warnings = [r for r in failures if r.severity.value == "warning"]
        if not failures:
            lint_display = "[bold]Lint[/bold]\n  [score-good]All checks passed[/score-good]"
        else:
            lines = ["[bold]Lint[/bold]"]
            if errors:
                lines.append(f"  [score-bad]{len(errors)} error(s)[/score-bad]")
            if warnings:
                lines.append(f"  [score-warn]{len(warnings)} warning(s)[/score-warn]")
            for f in failures[:3]:
                lines.append(f"  [dim]{f.rule}: {f.message}[/dim]")
            if len(failures) > 3:
                lines.append(f"  [dim]...and {len(failures) - 3} more[/dim]")
            lint_display = "\n".join(lines)
        self.query_one("#lint-score", Static).update(lint_display)

        # A11y
        a11y_result = self._a11y.check(text)
        if a11y_result.passed:
            a11y_display = "[bold]Accessibility[/bold]\n  [score-good]Pass[/score-good]"
        else:
            lines = ["[bold]Accessibility[/bold]"]
            critical = a11y_result.critical_issues
            high = a11y_result.high_issues
            if critical:
                lines.append(f"  [score-bad]{len(critical)} critical[/score-bad]")
            if high:
                lines.append(f"  [score-warn]{len(high)} high[/score-warn]")
            for issue in (critical + high)[:3]:
                lines.append(f"  [dim]{issue.rule}[/dim]")
            a11y_display = "\n".join(lines)
        self.query_one("#a11y-score", Static).update(a11y_display)
