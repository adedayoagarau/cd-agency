"""Status bar — footer showing active agent, preset, tokens, and mode."""

from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static


class StatusBar(Widget):
    """Bottom status bar for the studio."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
        background: $primary;
        color: $text;
        padding: 0 2;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._agent: str = "No agent selected"
        self._preset: str = "default"
        self._tokens: int = 0
        self._memory_count: int = 0
        self._mode: str = "Chat"

    def compose(self):
        yield Static(self._build_text(), id="status-text")

    def set_agent(self, name: str) -> None:
        self._agent = name
        self._refresh()

    def set_preset(self, name: str) -> None:
        self._preset = name
        self._refresh()

    def set_tokens(self, count: int) -> None:
        self._tokens = count
        self._refresh()

    def set_memory_count(self, count: int) -> None:
        self._memory_count = count
        self._refresh()

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self._refresh()

    def _build_text(self) -> str:
        return (
            f" {self._agent}  │  preset: {self._preset}  │  "
            f"tokens: {self._tokens}  │  memory: {self._memory_count}  │  "
            f"mode: {self._mode}"
        )

    def _refresh(self) -> None:
        try:
            self.query_one("#status-text", Static).update(self._build_text())
        except Exception:
            pass
