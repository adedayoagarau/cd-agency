"""CLI entry point for the CD Agency."""

from __future__ import annotations

import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from runtime.config import Config
from runtime.registry import AgentRegistry
from runtime.runner import AgentRunner

console = Console()


def _get_registry(agents_dir: str | None = None) -> AgentRegistry:
    """Build the agent registry from the configured directory."""
    from pathlib import Path
    config = Config.from_env()
    directory = Path(agents_dir) if agents_dir else config.agents_dir
    return AgentRegistry.from_directory(directory)


@click.group()
@click.version_option(version="0.1.0", prog_name="cd-agency")
def main() -> None:
    """Content Design Agency — AI-powered content design agents."""
    pass


# --- Agent commands ---

@main.group()
def agent() -> None:
    """Run and manage content design agents."""
    pass


@agent.command("list")
@click.option("--tag", help="Filter agents by tag")
@click.option("--difficulty", type=click.Choice(["beginner", "intermediate", "advanced"]))
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def agent_list(tag: str | None, difficulty: str | None, as_json: bool) -> None:
    """List all available agents."""
    registry = _get_registry()
    agents = registry.list_all()

    if tag:
        agents = [a for a in agents if tag.lower() in a.tags]
    if difficulty:
        agents = [a for a in agents if a.difficulty_level == difficulty]

    if as_json:
        data = [{"name": a.name, "slug": a.slug, "description": a.description,
                 "tags": a.tags, "difficulty": a.difficulty_level} for a in agents]
        click.echo(json.dumps(data, indent=2))
        return

    table = Table(title=f"Content Design Agents ({len(agents)})")
    table.add_column("Agent", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Difficulty", style="yellow")
    table.add_column("Tags", style="dim")

    for a in agents:
        table.add_row(a.slug, a.description, a.difficulty_level, ", ".join(a.tags[:3]))

    console.print(table)


@agent.command("info")
@click.argument("name")
def agent_info(name: str) -> None:
    """Show detailed information about an agent."""
    registry = _get_registry()
    a = registry.get(name)

    if not a:
        console.print(f"[red]Agent not found: '{name}'[/red]")
        console.print("Run [cyan]cd-agency agent list[/cyan] to see available agents.")
        sys.exit(1)

    console.print(f"\n[bold cyan]{a.name}[/bold cyan] (v{a.version})")
    console.print(f"[dim]{a.description}[/dim]\n")

    console.print("[bold]Required Inputs:[/bold]")
    for inp in a.get_required_inputs():
        console.print(f"  - [green]{inp.name}[/green] ({inp.type}): {inp.description}")

    optional = a.get_optional_inputs()
    if optional:
        console.print("\n[bold]Optional Inputs:[/bold]")
        for inp in optional:
            console.print(f"  - [yellow]{inp.name}[/yellow] ({inp.type}): {inp.description}")

    console.print("\n[bold]Outputs:[/bold]")
    for out in a.outputs:
        console.print(f"  - [blue]{out.name}[/blue] ({out.type}): {out.description}")

    if a.related_agents:
        console.print(f"\n[bold]Related Agents:[/bold] {', '.join(a.related_agents)}")

    console.print(f"\n[bold]Tags:[/bold] {', '.join(a.tags)}")
    console.print(f"[bold]Difficulty:[/bold] {a.difficulty_level}")
    console.print(f"[bold]Source:[/bold] {a.source_file}\n")


@agent.command("run")
@click.argument("name")
@click.option("--input", "-i", "input_text", help="Inline text input (maps to first required field)")
@click.option("--file", "-f", "input_file", type=click.Path(exists=True), help="Read input from file")
@click.option("--field", "-F", multiple=True, help="Set a specific field: --field name=value")
@click.option("--model", "-m", help="Override the model")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def agent_run(
    name: str,
    input_text: str | None,
    input_file: str | None,
    field: tuple[str, ...],
    model: str | None,
    as_json: bool,
) -> None:
    """Run an agent with the given input."""
    config = Config.from_env()
    errors = config.validate()
    if errors:
        for err in errors:
            console.print(f"[red]Config error: {err}[/red]")
        sys.exit(1)

    registry = _get_registry()
    a = registry.get(name)
    if not a:
        console.print(f"[red]Agent not found: '{name}'[/red]")
        sys.exit(1)

    # Build input dict
    user_input = _build_input(a, input_text, input_file, field)

    console.print(f"[dim]Running {a.name}...[/dim]")

    runner = AgentRunner(config)
    kwargs: dict[str, Any] = {}
    if model:
        kwargs["model"] = model

    try:
        result = runner.run(a, user_input, **kwargs)
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({
            "agent": a.name,
            "model": result.model,
            "content": result.content,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "latency_ms": round(result.latency_ms, 1),
        }, indent=2))
    else:
        console.print(f"\n{result.content}")
        console.print(f"\n[dim]Model: {result.model} | Tokens: {result.input_tokens}→{result.output_tokens} | {result.latency_ms:.0f}ms[/dim]")


# --- Workflow commands ---

@main.group()
def workflow() -> None:
    """Run multi-agent workflow pipelines."""
    pass


def _get_workflows() -> list:
    from pathlib import Path
    from runtime.workflow import load_workflows_from_directory
    return load_workflows_from_directory(Path("workflows"))


@workflow.command("list")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def workflow_list(as_json: bool) -> None:
    """List all available workflows."""
    workflows = _get_workflows()

    if as_json:
        data = [{"name": w.name, "slug": w.slug, "description": w.description,
                 "steps": len(w.steps)} for w in workflows]
        click.echo(json.dumps(data, indent=2))
        return

    table = Table(title=f"Workflows ({len(workflows)})")
    table.add_column("Workflow", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Steps", style="yellow", justify="center")

    for w in workflows:
        table.add_row(w.slug, w.description.strip()[:80], str(len(w.steps)))

    console.print(table)


@workflow.command("info")
@click.argument("name")
def workflow_info(name: str) -> None:
    """Show detailed information about a workflow."""
    workflows = _get_workflows()
    wf = next((w for w in workflows if w.slug == name or w.name.lower() == name.lower()), None)

    if not wf:
        console.print(f"[red]Workflow not found: '{name}'[/red]")
        console.print("Run [cyan]cd-agency workflow list[/cyan] to see available workflows.")
        sys.exit(1)

    console.print(f"\n[bold cyan]{wf.name}[/bold cyan]")
    console.print(f"[dim]{wf.description.strip()}[/dim]\n")

    console.print("[bold]Steps:[/bold]")
    for i, step in enumerate(wf.steps, 1):
        parallel = f" [dim](parallel: {step.parallel_group})[/dim]" if step.parallel_group else ""
        condition = f" [dim](if: {step.condition})[/dim]" if step.condition else ""
        console.print(f"  {i}. [green]{step.name}[/green] → agent: [cyan]{step.agent}[/cyan]{parallel}{condition}")

        if step.input_map:
            for field, source in step.input_map.items():
                src_display = source if len(str(source)) < 50 else str(source)[:47] + "..."
                console.print(f"     {field}: {src_display}")

    console.print(f"\n[bold]Source:[/bold] {wf.source_file}\n")


@workflow.command("run")
@click.argument("name")
@click.option("--field", "-F", multiple=True, help="Set input field: --field key=value")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def workflow_run(name: str, field: tuple[str, ...], as_json: bool) -> None:
    """Run a multi-agent workflow pipeline."""
    config = Config.from_env()
    errors = config.validate()
    if errors:
        for err in errors:
            console.print(f"[red]Config error: {err}[/red]")
        sys.exit(1)

    workflows = _get_workflows()
    wf = next((w for w in workflows if w.slug == name or w.name.lower() == name.lower()), None)

    if not wf:
        console.print(f"[red]Workflow not found: '{name}'[/red]")
        sys.exit(1)

    # Build input
    workflow_input: dict[str, Any] = {}
    for f in field:
        if "=" in f:
            key, value = f.split("=", 1)
            workflow_input[key.strip()] = value.strip()

    from runtime.workflow import WorkflowEngine

    registry = _get_registry()

    def on_step_start(step_name: str, agent_name: str) -> None:
        if not as_json:
            console.print(f"  [dim]Step: {step_name} → {agent_name}...[/dim]")

    def on_step_complete(step_name: str, result: Any) -> None:
        if not as_json:
            status = "[green]done[/green]" if not result.skipped else "[yellow]skipped[/yellow]"
            if result.error:
                status = f"[red]error: {result.error}[/red]"
            console.print(f"  [dim]  → {status}[/dim]")

    engine = WorkflowEngine(
        registry=registry,
        config=config,
        on_step_start=on_step_start,
        on_step_complete=on_step_complete,
    )

    if not as_json:
        console.print(f"[bold]Running workflow: {wf.name}[/bold] ({len(wf.steps)} steps)\n")

    try:
        result = engine.run(wf, workflow_input)
    except Exception as e:
        console.print(f"[red]Workflow error: {e}[/red]")
        sys.exit(1)

    if as_json:
        data = {
            "workflow": wf.name,
            "steps": [
                {
                    "step": r.step_name,
                    "agent": r.agent_name,
                    "skipped": r.skipped,
                    "error": r.error,
                    "content": r.output.content if r.output else "",
                }
                for r in result.step_results
            ],
            "total_tokens": result.total_tokens,
            "total_latency_ms": round(result.total_latency_ms, 1),
        }
        click.echo(json.dumps(data, indent=2))
    else:
        console.print(f"\n[bold]Results:[/bold]")
        for r in result.step_results:
            if r.skipped:
                console.print(f"\n[yellow]--- {r.step_name} (skipped) ---[/yellow]")
            elif r.error:
                console.print(f"\n[red]--- {r.step_name} (error: {r.error}) ---[/red]")
            else:
                console.print(f"\n[cyan]--- {r.step_name} ({r.agent_name}) ---[/cyan]")
                console.print(r.output.content)

        tokens = result.total_tokens
        console.print(f"\n[dim]Total: {tokens['input']}→{tokens['output']} tokens | {result.total_latency_ms:.0f}ms[/dim]")


def _build_input(
    agent: Agent,
    input_text: str | None,
    input_file: str | None,
    fields: tuple[str, ...],
) -> dict[str, Any]:
    """Build the input dict from CLI arguments."""
    user_input: dict[str, Any] = {}

    # Parse --field key=value pairs
    for f in fields:
        if "=" in f:
            key, value = f.split("=", 1)
            user_input[key.strip()] = value.strip()

    # If --file, read it as the primary input
    if input_file:
        from pathlib import Path
        content = Path(input_file).read_text(encoding="utf-8")
        if agent.inputs:
            user_input.setdefault(agent.inputs[0].name, content)

    # If --input, use as the primary input
    if input_text:
        if agent.inputs:
            user_input.setdefault(agent.inputs[0].name, input_text)

    # Read from stdin if no input provided and stdin is piped
    if not user_input and not sys.stdin.isatty():
        stdin_content = sys.stdin.read().strip()
        if stdin_content and agent.inputs:
            user_input[agent.inputs[0].name] = stdin_content

    return user_input


if __name__ == "__main__":
    main()
