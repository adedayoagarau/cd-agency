"""Chat panel — conversational interface for multi-turn agent interaction."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Static


class ChatMessageSent(Message):
    """Posted when the user sends a chat message."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class ScoreRequested(Message):
    """Posted when the user clicks Score on an agent message."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class AcceptRequested(Message):
    """Posted when the user clicks Accept on an agent message."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class ChatMessage(Static):
    """A single message in the chat history."""

    DEFAULT_CSS = """
    ChatMessage {
        padding: 1 2;
        margin: 0 0 1 0;
    }
    ChatMessage.user-message {
        background: $primary 20%;
        border-left: thick $primary;
    }
    ChatMessage.agent-message {
        background: $success 10%;
        border-left: thick $success;
    }
    """

    def __init__(self, content: str, role: str, **kwargs) -> None:
        self.role = role
        self.content_text = content
        prefix = "[bold cyan]You[/bold cyan]" if role == "user" else "[bold green]Agent[/bold green]"
        super().__init__(f"{prefix}\n{content}", **kwargs)


class ChatPanel(Widget):
    """Multi-turn chat interface with message history and input."""

    DEFAULT_CSS = """
    ChatPanel {
        height: 1fr;
    }
    ChatPanel #chat-scroll {
        height: 1fr;
    }
    ChatPanel #chat-input-bar {
        height: auto;
        dock: bottom;
        padding: 1;
        background: $surface;
        border-top: solid $primary-background;
    }
    ChatPanel #chat-input {
        width: 1fr;
    }
    ChatPanel #chat-actions {
        height: auto;
        dock: bottom;
        layout: horizontal;
        padding: 0 1;
        background: $surface;
    }
    ChatPanel #chat-actions Button {
        margin: 0 1 0 0;
    }
    ChatPanel .empty-chat {
        text-align: center;
        color: $text-muted;
        padding: 4;
    }
    ChatPanel .loading {
        text-align: center;
        color: $accent;
        padding: 2;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._messages: list[dict[str, str]] = []
        self._last_agent_text: str = ""
        self._is_loading: bool = False

    @property
    def messages(self) -> list[dict[str, str]]:
        """Return the conversation history."""
        return list(self._messages)

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="chat-scroll"):
            yield Static(
                "Select an agent and start typing to begin a conversation.",
                classes="empty-chat",
                id="empty-hint",
            )
        with Vertical(id="chat-actions"):
            yield Button("Accept", id="btn-accept", variant="success", disabled=True)
            yield Button("Copy", id="btn-copy", variant="default", disabled=True)
            yield Button("Score", id="btn-score", variant="primary", disabled=True)
        yield Input(placeholder="Type a message...", id="chat-input")

    def add_user_message(self, text: str) -> None:
        """Add a user message to the chat."""
        self._messages.append({"role": "user", "content": text})
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        hint = self.query_one("#empty-hint", Static)
        hint.display = False
        scroll.mount(ChatMessage(text, "user", classes="user-message"))
        scroll.scroll_end(animate=False)

    def add_agent_message(self, text: str) -> None:
        """Add an agent response to the chat."""
        self._messages.append({"role": "assistant", "content": text})
        self._last_agent_text = text
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        scroll.mount(ChatMessage(text, "assistant", classes="agent-message"))
        scroll.scroll_end(animate=False)
        # Enable action buttons
        self.query_one("#btn-accept", Button).disabled = False
        self.query_one("#btn-copy", Button).disabled = False
        self.query_one("#btn-score", Button).disabled = False

    def set_loading(self, loading: bool) -> None:
        """Show or hide loading indicator."""
        self._is_loading = loading
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        existing = self.query(".loading")
        for el in existing:
            el.remove()
        if loading:
            scroll.mount(Static("Thinking...", classes="loading"))
            scroll.scroll_end(animate=False)

    def clear_chat(self) -> None:
        """Clear all messages."""
        self._messages.clear()
        self._last_agent_text = ""
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        for child in list(scroll.children):
            if child.id != "empty-hint":
                child.remove()
        self.query_one("#empty-hint", Static).display = True
        self.query_one("#btn-accept", Button).disabled = True
        self.query_one("#btn-copy", Button).disabled = True
        self.query_one("#btn-score", Button).disabled = True

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat-input" and event.value.strip():
            text = event.value.strip()
            event.input.value = ""
            self.add_user_message(text)
            self.post_message(ChatMessageSent(text))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-accept" and self._last_agent_text:
            self.post_message(AcceptRequested(self._last_agent_text))
        elif event.button.id == "btn-copy" and self._last_agent_text:
            try:
                import pyperclip
                pyperclip.copy(self._last_agent_text)
            except ImportError:
                pass  # No clipboard support
        elif event.button.id == "btn-score" and self._last_agent_text:
            self.post_message(ScoreRequested(self._last_agent_text))
