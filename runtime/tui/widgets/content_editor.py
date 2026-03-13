"""Content editor — structured text editing with live metrics."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, TextArea


class ContentChanged(Message):
    """Posted when the editor content changes (debounced by app)."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class ContentEditor(Widget):
    """Text editor with live character/word count for structured input mode."""

    DEFAULT_CSS = """
    ContentEditor {
        height: 1fr;
    }
    ContentEditor TextArea {
        height: 1fr;
    }
    ContentEditor .editor-stats {
        height: 1;
        dock: bottom;
        background: $surface;
        color: $text-muted;
        padding: 0 2;
    }
    """

    def __init__(self, initial_content: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._initial_content = initial_content

    @property
    def text(self) -> str:
        """Get the current editor content."""
        return self.query_one("#editor-area", TextArea).text

    @text.setter
    def text(self, value: str) -> None:
        """Set the editor content."""
        area = self.query_one("#editor-area", TextArea)
        area.load_text(value)

    def compose(self) -> ComposeResult:
        yield TextArea(self._initial_content, id="editor-area", language=None)
        yield Static("Words: 0  Chars: 0", id="editor-stats", classes="editor-stats")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        text = event.text_area.text
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.query_one("#editor-stats", Static).update(
            f"Words: {words}  Chars: {chars}"
        )
        self.post_message(ContentChanged(text))
