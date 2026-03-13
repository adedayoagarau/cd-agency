"""Agent browser sidebar — searchable list of all content design agents."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Label, ListItem, ListView, Static

from runtime.agent import Agent


class AgentSelected(Message):
    """Posted when the user selects an agent from the browser."""

    def __init__(self, agent: Agent) -> None:
        super().__init__()
        self.agent = agent


class AgentBrowser(Widget):
    """Searchable agent list grouped by primary tag."""

    DEFAULT_CSS = """
    AgentBrowser {
        width: 28;
        dock: left;
        background: $surface;
        border-right: solid $primary-background;
        padding: 0 1;
    }
    AgentBrowser .browser-title {
        text-style: bold;
        color: $text;
        padding: 1 0;
    }
    AgentBrowser #agent-search {
        margin-bottom: 1;
    }
    AgentBrowser .tag-header {
        color: $accent;
        text-style: bold;
        padding: 1 0 0 0;
    }
    AgentBrowser .agent-item {
        padding: 0 1;
    }
    AgentBrowser .agent-item:hover {
        background: $boost;
    }
    """

    def __init__(self, agents: list[Agent] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._agents: list[Agent] = agents or []
        self._filtered: list[Agent] = list(self._agents)

    def set_agents(self, agents: list[Agent]) -> None:
        """Update the agent list and refresh."""
        self._agents = agents
        self._filtered = list(agents)
        self._rebuild_list()

    def compose(self) -> ComposeResult:
        yield Static("AGENTS", classes="browser-title")
        yield Input(placeholder="Search agents...", id="agent-search")
        yield ListView(id="agent-list")

    def on_mount(self) -> None:
        self._rebuild_list()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "agent-search":
            query = event.value.lower().strip()
            if query:
                self._filtered = [
                    a for a in self._agents
                    if query in a.name.lower()
                    or query in a.description.lower()
                    or any(query in t for t in a.tags)
                ]
            else:
                self._filtered = list(self._agents)
            self._rebuild_list()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._filtered):
            self.post_message(AgentSelected(self._filtered[idx]))

    def _rebuild_list(self) -> None:
        list_view = self.query_one("#agent-list", ListView)
        list_view.clear()
        for agent in self._filtered:
            tag = agent.tags[0] if agent.tags else "general"
            item = ListItem(
                Label(f"[bold]{agent.name}[/bold]\n[dim]{tag}[/dim]"),
                classes="agent-item",
            )
            list_view.append(item)
