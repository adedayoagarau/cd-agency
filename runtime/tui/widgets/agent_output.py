"""Agent output panel — displays agent results in form mode."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, RichLog, Static, TabbedContent, TabPane


class OutputAccepted(Message):
    """Posted when the user accepts agent output (copies to editor)."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class AgentOutputPanel(Widget):
    """Tabbed output display with Output and Diff views."""

    DEFAULT_CSS = """
    AgentOutputPanel {
        height: 2fr;
        border-top: solid $primary-background;
    }
    AgentOutputPanel .output-actions {
        height: auto;
        dock: bottom;
        layout: horizontal;
        padding: 0 1;
        background: $surface;
    }
    AgentOutputPanel .output-actions Button {
        margin: 0 1 0 0;
    }
    AgentOutputPanel .output-hint {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_output: str = ""
        self._input_text: str = ""

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Output", id="output-tab"):
                yield RichLog(id="output-log", wrap=True, markup=True)
            with TabPane("Diff", id="diff-tab"):
                yield RichLog(id="diff-log", wrap=True, markup=True)
        with Horizontal(classes="output-actions"):
            yield Button("Accept", id="output-accept", variant="success", disabled=True)
            yield Button("Copy", id="output-copy", variant="default", disabled=True)

    def show_output(self, text: str, input_text: str = "") -> None:
        """Display agent output and generate diff."""
        self._current_output = text
        self._input_text = input_text

        output_log = self.query_one("#output-log", RichLog)
        output_log.clear()
        output_log.write(text)

        # Simple diff display
        diff_log = self.query_one("#diff-log", RichLog)
        diff_log.clear()
        if input_text:
            diff_log.write("[red]- " + input_text + "[/red]")
            diff_log.write("[green]+ " + text + "[/green]")
        else:
            diff_log.write("[dim]No input to compare against.[/dim]")

        self.query_one("#output-accept", Button).disabled = False
        self.query_one("#output-copy", Button).disabled = False

    def show_loading(self) -> None:
        """Show loading state."""
        output_log = self.query_one("#output-log", RichLog)
        output_log.clear()
        output_log.write("[dim]Running agent...[/dim]")

    def clear(self) -> None:
        """Clear the output display."""
        self._current_output = ""
        self._input_text = ""
        self.query_one("#output-log", RichLog).clear()
        self.query_one("#diff-log", RichLog).clear()
        self.query_one("#output-accept", Button).disabled = True
        self.query_one("#output-copy", Button).disabled = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "output-accept" and self._current_output:
            self.post_message(OutputAccepted(self._current_output))
        elif event.button.id == "output-copy" and self._current_output:
            try:
                import pyperclip
                pyperclip.copy(self._current_output)
            except ImportError:
                pass
