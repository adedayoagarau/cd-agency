"""Memory panel — view and search project memory entries."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Input, Static

from runtime.memory import ProjectMemory


class MemoryPanel(Widget):
    """Searchable project memory viewer — replaces agent browser when toggled."""

    DEFAULT_CSS = """
    MemoryPanel {
        width: 28;
        dock: left;
        background: $surface;
        border-right: solid $primary-background;
        padding: 0 1;
        display: none;
    }
    MemoryPanel .memory-title {
        text-style: bold;
        color: $text;
        padding: 1 0;
    }
    MemoryPanel #memory-search {
        margin-bottom: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._memory: ProjectMemory | None = None

    def set_memory(self, memory: ProjectMemory) -> None:
        """Load memory entries into the table."""
        self._memory = memory
        self._rebuild_table()

    def compose(self) -> ComposeResult:
        yield Static("MEMORY", classes="memory-title")
        yield Input(placeholder="Search memory...", id="memory-search")
        yield DataTable(id="memory-table")

    def on_mount(self) -> None:
        table = self.query_one("#memory-table", DataTable)
        table.add_columns("Key", "Value", "Category")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "memory-search":
            self._rebuild_table(event.value.lower().strip())

    def _rebuild_table(self, query: str = "") -> None:
        table = self.query_one("#memory-table", DataTable)
        table.clear()
        if not self._memory:
            return
        for key, entry in self._memory.entries.items():
            if query and query not in key.lower() and query not in entry.value.lower():
                continue
            # Truncate long values for display
            value = entry.value[:40] + "..." if len(entry.value) > 40 else entry.value
            table.add_row(key, value, entry.category)
