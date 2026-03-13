"""Command palette provider — indexes agents, presets, workflows, and actions."""

from __future__ import annotations

from textual.command import Hit, Hits, Provider

from runtime.agent import Agent


class StudioCommandProvider(Provider):
    """Provides command palette entries for agents, presets, and actions."""

    async def search(self, query: str) -> Hits:
        """Search all indexed commands."""
        app = self.app
        query_lower = query.lower()

        # Agent commands
        agents: list[Agent] = getattr(app, "_agents", [])
        for agent in agents:
            text = f"Run Agent: {agent.name}"
            if query_lower in text.lower():
                yield Hit(
                    score=_match_score(query_lower, text.lower()),
                    match_display=text,
                    command=_make_agent_callback(app, agent),
                    help=agent.description,
                )

        # Preset commands
        presets = ["Material Design", "Apple HIG", "Polaris", "Atlassian"]
        for preset in presets:
            text = f"Preset: {preset}"
            if query_lower in text.lower():
                yield Hit(
                    score=_match_score(query_lower, text.lower()),
                    match_display=text,
                    command=_make_preset_callback(app, preset),
                    help=f"Switch to {preset} design system",
                )

        # Mode commands
        for mode in ["Chat", "Form"]:
            text = f"Mode: {mode}"
            if query_lower in text.lower():
                yield Hit(
                    score=_match_score(query_lower, text.lower()),
                    match_display=text,
                    command=_make_mode_callback(app, mode),
                    help=f"Switch to {mode} mode",
                )

        # Action commands
        actions = [
            ("Clear Chat", "Clear the conversation history"),
            ("Score Content", "Run all scoring tools on current content"),
            ("Toggle Memory", "Show/hide memory panel"),
        ]
        for action_name, help_text in actions:
            text = f"Action: {action_name}"
            if query_lower in text.lower():
                yield Hit(
                    score=_match_score(query_lower, text.lower()),
                    match_display=text,
                    command=_make_action_callback(app, action_name),
                    help=help_text,
                )


def _match_score(query: str, text: str) -> int:
    """Simple relevance score — higher is better."""
    if query == text:
        return 100
    if text.startswith(query):
        return 80
    return 50


def _make_agent_callback(app, agent: Agent):
    """Create a callback that selects an agent."""
    async def callback() -> None:
        app.select_agent(agent)
    return callback


def _make_preset_callback(app, preset: str):
    """Create a callback that switches preset."""
    async def callback() -> None:
        app.switch_preset(preset)
    return callback


def _make_mode_callback(app, mode: str):
    """Create a callback that switches mode."""
    async def callback() -> None:
        app.switch_mode_to(mode)
    return callback


def _make_action_callback(app, action: str):
    """Create a callback for studio actions."""
    async def callback() -> None:
        app.run_action_command(action)
    return callback
