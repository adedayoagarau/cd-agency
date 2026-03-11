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
@click.version_option(version="0.2.0", prog_name="cd-agency")
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


@agent.command("create")
def agent_create() -> None:
    """Create a new custom agent with an interactive wizard."""
    from pathlib import Path
    from runtime.agent_builder import build_agent_interactive
    config = Config.from_env()
    build_agent_interactive(config.agents_dir)


@agent.command("import")
@click.argument("source", type=click.Path(exists=True))
def agent_import(source: str) -> None:
    """Import an agent from a file."""
    from runtime.agent_builder import import_agent
    config = Config.from_env()
    import_agent(source, config.agents_dir)


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


# --- Score commands ---

@main.group()
def score() -> None:
    """Score and evaluate content quality."""
    pass


def _get_input_text(input_text: str | None, input_file: str | None) -> str:
    """Get text from --input, --file, or stdin."""
    if input_text:
        return input_text
    if input_file:
        from pathlib import Path
        return Path(input_file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    click.echo("Error: Provide text via --input, --file, or stdin pipe.", err=True)
    sys.exit(1)


@score.command("readability")
@click.option("--input", "-i", "input_text", help="Text to score")
@click.option("--file", "-f", "input_file", type=click.Path(exists=True), help="Read from file")
@click.option("--compare", "-c", "compare_text", help="'Before' text to compare against")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def score_readability(
    input_text: str | None, input_file: str | None,
    compare_text: str | None, as_json: bool,
) -> None:
    """Score text for readability metrics (Flesch-Kincaid, etc.)."""
    from tools.scoring import ReadabilityScorer
    from tools.report import ScoringReport, ReportFormat

    text = _get_input_text(input_text, input_file)
    scorer = ReadabilityScorer()

    if compare_text:
        report = ScoringReport(
            text=text,
            readability=scorer.score(text),
            before_readability=scorer.score(compare_text),
        )
    else:
        report = ScoringReport(text=text, readability=scorer.score(text))

    fmt = ReportFormat.JSON if as_json else ReportFormat.TEXT
    click.echo(report.render(fmt))


@score.command("lint")
@click.option("--input", "-i", "input_text", help="Text to lint")
@click.option("--file", "-f", "input_file", type=click.Path(exists=True), help="Read from file")
@click.option("--type", "-t", "content_type", default="general",
              type=click.Choice(["general", "cta", "button", "error", "notification", "microcopy"]),
              help="Content type for type-specific rules")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def score_lint(
    input_text: str | None, input_file: str | None,
    content_type: str, as_json: bool,
) -> None:
    """Run content lint rules on text."""
    from tools.linter import ContentLinter
    from tools.report import ScoringReport, ReportFormat

    text = _get_input_text(input_text, input_file)
    linter = ContentLinter()
    results = linter.lint(text, content_type=content_type)

    report = ScoringReport(text=text, lint_results=results)
    fmt = ReportFormat.JSON if as_json else ReportFormat.TEXT
    click.echo(report.render(fmt))


@score.command("a11y")
@click.option("--input", "-i", "input_text", help="Text to check")
@click.option("--file", "-f", "input_file", type=click.Path(exists=True), help="Read from file")
@click.option("--target-grade", default=8.0, help="Target reading grade level (default: 8)")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def score_a11y(
    input_text: str | None, input_file: str | None,
    target_grade: float, as_json: bool,
) -> None:
    """Check text for accessibility issues (WCAG compliance)."""
    from tools.a11y_checker import A11yChecker
    from tools.report import ScoringReport, ReportFormat

    text = _get_input_text(input_text, input_file)
    checker = A11yChecker(target_grade=target_grade)
    result = checker.check(text)

    report = ScoringReport(text=text, a11y_result=result)
    fmt = ReportFormat.JSON if as_json else ReportFormat.TEXT
    click.echo(report.render(fmt))


@score.command("voice")
@click.option("--input", "-i", "input_text", help="Text to check")
@click.option("--file", "-f", "input_file", type=click.Path(exists=True), help="Read from file")
@click.option("--guide", "-g", type=click.Path(exists=True), help="Brand voice YAML guide")
@click.option("--no-llm", is_flag=True, help="Use rule-based check (no API call)")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def score_voice(
    input_text: str | None, input_file: str | None,
    guide: str | None, no_llm: bool, as_json: bool,
) -> None:
    """Check text against a brand voice guide."""
    from tools.voice_checker import VoiceChecker, VoiceProfile
    from tools.report import ScoringReport, ReportFormat

    text = _get_input_text(input_text, input_file)

    if not guide:
        click.echo("Error: --guide is required. Provide a brand voice YAML file.", err=True)
        sys.exit(1)

    profile = VoiceProfile.from_yaml(guide)
    checker = VoiceChecker()

    if no_llm:
        result = checker.check_without_llm(text, profile)
    else:
        result = checker.check(text, profile)

    report = ScoringReport(text=text, voice_result=result)
    fmt = ReportFormat.JSON if as_json else ReportFormat.TEXT
    click.echo(report.render(fmt))


@score.command("all")
@click.option("--input", "-i", "input_text", help="Text to score")
@click.option("--file", "-f", "input_file", type=click.Path(exists=True), help="Read from file")
@click.option("--type", "-t", "content_type", default="general",
              type=click.Choice(["general", "cta", "button", "error", "notification", "microcopy"]))
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
@click.option("--markdown", "as_md", is_flag=True, help="Output as Markdown")
def score_all(
    input_text: str | None, input_file: str | None,
    content_type: str, as_json: bool, as_md: bool,
) -> None:
    """Run all scoring tools (readability + lint + a11y)."""
    from tools.scoring import ReadabilityScorer
    from tools.linter import ContentLinter
    from tools.a11y_checker import A11yChecker
    from tools.report import ScoringReport, ReportFormat

    text = _get_input_text(input_text, input_file)

    report = ScoringReport(
        text=text,
        readability=ReadabilityScorer().score(text),
        lint_results=ContentLinter().lint(text, content_type=content_type),
        a11y_result=A11yChecker().check(text),
    )

    if as_json:
        fmt = ReportFormat.JSON
    elif as_md:
        fmt = ReportFormat.MARKDOWN
    else:
        fmt = ReportFormat.TEXT

    click.echo(report.render(fmt))


# --- Export command ---

@main.command("export")
@click.option("--input", "-i", "input_text", help="Original (before) text")
@click.option("--output", "-o", "output_text", help="Improved (after) text")
@click.option("--id", "entry_id", default="1", help="Content entry ID")
@click.option("--context", default="", help="Context description")
@click.option("--agent", "agent_name", default="", help="Agent that produced the output")
@click.option("--format", "-f", "fmt",
              type=click.Choice(["json", "csv", "markdown", "xliff"]),
              default="json", help="Export format")
def export_cmd(
    input_text: str | None, output_text: str | None,
    entry_id: str, context: str, agent_name: str, fmt: str,
) -> None:
    """Export content in various formats (JSON, CSV, Markdown, XLIFF)."""
    from tools.export import ContentEntry, ExportFormat, export_entries

    if not input_text or not output_text:
        click.echo("Error: Both --input and --output are required.", err=True)
        sys.exit(1)

    entries = [ContentEntry(
        id=entry_id,
        source=input_text,
        target=output_text,
        context=context,
        agent=agent_name,
    )]

    export_fmt = ExportFormat(fmt)
    click.echo(export_entries(entries, export_fmt))


# --- Preset command ---

@main.command("presets")
def list_presets() -> None:
    """List available design system presets."""
    from pathlib import Path

    presets_dir = Path("presets")
    if not presets_dir.exists():
        console.print("[yellow]No presets directory found.[/yellow]")
        return

    table = Table(title="Design System Presets")
    table.add_column("Preset", style="cyan")
    table.add_column("File", style="dim")

    for f in sorted(presets_dir.glob("*.yaml")):
        name = f.stem.replace("-", " ").title()
        table.add_row(name, str(f))

    console.print(table)
    console.print(f"\n[dim]Use with: cd-agency score voice --guide presets/<name>.yaml[/dim]")


# --- Memory commands ---

@main.group()
def memory() -> None:
    """Manage project-level memory (terminology, decisions, patterns)."""
    pass


@memory.command("show")
@click.option("--category", "-c", help="Filter by category (terminology, voice, pattern, decision)")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def memory_show(category: str | None, as_json: bool) -> None:
    """Show stored project memory."""
    from runtime.memory import ProjectMemory

    mem = ProjectMemory.load()
    if not mem.entries:
        console.print("[dim]No memory stored yet.[/dim]")
        return

    if as_json:
        click.echo(json.dumps(mem.to_dict(), indent=2))
        return

    entries = mem.recall_by_category(category) if category else list(mem.entries.values())
    table = Table(title=f"Project Memory ({len(entries)} entries)")
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    table.add_column("Category", style="dim")
    table.add_column("Agent", style="dim")

    for e in entries:
        table.add_row(e.key, e.value, e.category, e.source_agent)

    console.print(table)


@memory.command("add")
@click.argument("key")
@click.argument("value")
@click.option("--category", "-c", default="decision",
              type=click.Choice(["terminology", "voice", "pattern", "decision"]))
@click.option("--agent", default="", help="Source agent name")
def memory_add(key: str, value: str, category: str, agent: str) -> None:
    """Add a memory entry."""
    from runtime.memory import ProjectMemory

    mem = ProjectMemory.load()
    mem.remember(key, value, category=category, source_agent=agent)
    console.print(f"[green]Remembered:[/green] {key} = {value} [{category}]")


@memory.command("clear")
@click.confirmation_option(prompt="Clear all project memory?")
def memory_clear() -> None:
    """Clear all project memory."""
    from runtime.memory import ProjectMemory

    mem = ProjectMemory.load()
    count = mem.clear()
    console.print(f"[yellow]Cleared {count} memory entries.[/yellow]")


@memory.command("export")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "csv"]), default="json")
def memory_export(fmt: str) -> None:
    """Export memory as JSON or CSV."""
    from runtime.memory import ProjectMemory

    mem = ProjectMemory.load()
    if fmt == "json":
        click.echo(json.dumps(mem.to_dict(), indent=2))
    else:
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Key", "Value", "Category", "Agent", "Timestamp"])
        for e in mem.entries.values():
            writer.writerow([e.key, e.value, e.category, e.source_agent, e.timestamp])
        click.echo(output.getvalue())


# --- Context commands ---

@main.group()
def context() -> None:
    """Manage product context (domain, audience, tone) for tailored suggestions."""
    pass


@context.command("show")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def context_show(as_json: bool) -> None:
    """Show the current product context."""
    config = Config.from_env()
    ctx = config.product_context

    if not ctx.is_configured():
        console.print("[dim]No product context configured yet.[/dim]")
        console.print("Run [cyan]cd-agency context init[/cyan] to set up your product context.")
        return

    if as_json:
        click.echo(json.dumps(ctx.to_dict(), indent=2))
        return

    console.print("\n[bold]Product Context[/bold]\n")
    if ctx.product_name:
        console.print(f"  [cyan]Product:[/cyan]  {ctx.product_name}")
    if ctx.description:
        console.print(f"  [cyan]About:[/cyan]    {ctx.description}")
    if ctx.domain:
        console.print(f"  [cyan]Domain:[/cyan]   {ctx.domain}")
    if ctx.audience:
        console.print(f"  [cyan]Audience:[/cyan] {ctx.audience}")
    if ctx.tone:
        console.print(f"  [cyan]Tone:[/cyan]     {ctx.tone}")
    if ctx.platform:
        console.print(f"  [cyan]Platform:[/cyan] {ctx.platform}")
    if ctx.guidelines:
        console.print(f"  [cyan]Guidelines:[/cyan]")
        for g in ctx.guidelines:
            console.print(f"    - {g}")
    console.print()


@context.command("init")
def context_init() -> None:
    """Interactively set up product context for your project."""
    from pathlib import Path

    console.print("\n[bold]Product Context Setup[/bold]")
    console.print("This helps agents tailor suggestions to your product.\n")

    product_name = click.prompt("Product name", default="")
    description = click.prompt("What does your product do? (1-2 sentences)", default="")
    domain = click.prompt("Domain (e.g. fintech, healthcare, e-commerce, SaaS)", default="")
    audience = click.prompt("Target audience (e.g. small business owners, developers)", default="")
    tone = click.prompt("Tone (e.g. professional but friendly, casual, formal)", default="")
    platform = click.prompt("Platform (e.g. web app, mobile app, desktop, multi-platform)", default="")

    guidelines_str = click.prompt(
        "Content guidelines, comma-separated (e.g. 'no jargon, use active voice')",
        default="",
    )
    guidelines = [g.strip() for g in guidelines_str.split(",") if g.strip()] if guidelines_str else []

    # Build the context dict
    context_data: dict[str, Any] = {}
    if product_name:
        context_data["product_name"] = product_name
    if description:
        context_data["description"] = description
    if domain:
        context_data["domain"] = domain
    if audience:
        context_data["audience"] = audience
    if tone:
        context_data["tone"] = tone
    if platform:
        context_data["platform"] = platform
    if guidelines:
        context_data["guidelines"] = guidelines

    if not context_data:
        console.print("[yellow]No context provided. Skipping.[/yellow]")
        return

    # Read existing config or create new
    config_path = Path(".cd-agency.yaml")
    existing: dict[str, Any] = {}
    if config_path.exists():
        import yaml as _yaml
        existing = _yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    existing["product_context"] = context_data

    import yaml as _yaml
    config_path.write_text(
        _yaml.dump(existing, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    console.print(f"\n[green]Product context saved to {config_path}[/green]")
    console.print("[dim]All agents will now use this context to tailor their suggestions.[/dim]\n")


@context.command("set")
@click.argument("key", type=click.Choice([
    "product_name", "description", "domain", "audience", "tone", "platform",
]))
@click.argument("value")
def context_set(key: str, value: str) -> None:
    """Set a single product context field."""
    from pathlib import Path
    import yaml as _yaml

    config_path = Path(".cd-agency.yaml")
    existing: dict[str, Any] = {}
    if config_path.exists():
        existing = _yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    if "product_context" not in existing:
        existing["product_context"] = {}

    existing["product_context"][key] = value

    config_path.write_text(
        _yaml.dump(existing, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    console.print(f"[green]Set {key} = {value}[/green]")


# --- Stats command ---

@main.command("stats")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
@click.option("--csv-output", "as_csv", is_flag=True, help="Output as CSV")
def stats_cmd(as_json: bool, as_csv: bool) -> None:
    """Show usage analytics dashboard."""
    from tools.analytics import Analytics

    analytics = Analytics.load()

    if as_json:
        click.echo(json.dumps(analytics.summary(), indent=2))
        return
    if as_csv:
        click.echo(analytics.export_csv())
        return

    if analytics.total_runs == 0:
        console.print("[dim]No usage data yet. Run some agents to see stats![/dim]")
        return

    summary = analytics.summary()
    console.print(f"\n[bold]CD Agency Usage Stats[/bold]")
    console.print(f"Total runs: [cyan]{summary['total_runs']}[/cyan]")
    console.print(f"Unique agents: [cyan]{summary['unique_agents_used']}[/cyan]")
    console.print(f"Total tokens: [cyan]{summary['total_tokens']:,}[/cyan]\n")

    if summary["top_agents"]:
        table = Table(title="Top Agents")
        table.add_column("Agent", style="cyan")
        table.add_column("Runs", justify="right")
        table.add_column("Avg Score", justify="right")
        for a in summary["top_agents"]:
            table.add_row(a["name"], str(a["runs"]), str(a["avg_score"]) if a["avg_score"] else "-")
        console.print(table)


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


# --- Interactive mode ---

@main.command("interactive")
def interactive_mode() -> None:
    """Guided interactive session — pick an agent, provide input, see results."""
    registry = _get_registry()
    agents = registry.list_all()

    console.print("\n[bold]Welcome to the Content Design Agency[/bold]")
    console.print("Let's find the right agent for your task.\n")

    # Show task categories
    categories = {
        "1": ("Writing or reviewing microcopy (buttons, labels, tooltips)", "microcopy-review-agent"),
        "2": ("Creating or improving CTAs", "cta-optimization-specialist"),
        "3": ("Writing error messages", "error-message-architect"),
        "4": ("Designing onboarding flows", "onboarding-flow-designer"),
        "5": ("Checking accessibility", "accessibility-content-auditor"),
        "6": ("Adjusting tone and voice", "tone-evaluation-agent"),
        "7": ("Writing for mobile", "mobile-ux-writer"),
        "8": ("Designing empty states", "empty-state-placeholder-specialist"),
        "9": ("Writing notifications", "notification-content-designer"),
        "10": ("General content design help", "content-designer-generalist"),
    }

    console.print("[bold]What are you working on?[/bold]")
    for key, (desc, _) in categories.items():
        console.print(f"  [cyan]{key:>2}[/cyan]. {desc}")

    choice = click.prompt("\nSelect a number", type=str, default="10")
    if choice not in categories:
        console.print("[yellow]Using generalist agent.[/yellow]")
        choice = "10"

    _, agent_slug = categories[choice]
    agent = registry.get(agent_slug)

    if not agent:
        console.print(f"[red]Agent not found: {agent_slug}[/red]")
        sys.exit(1)

    console.print(f"\n[bold cyan]Using: {agent.name}[/bold cyan]")
    console.print(f"[dim]{agent.description}[/dim]\n")

    # Collect inputs
    user_input: dict[str, Any] = {}
    for inp in agent.inputs:
        label = f"{inp.name}"
        if inp.description:
            label += f" ({inp.description})"
        if not inp.required:
            label += " [optional]"

        if inp.required:
            value = click.prompt(f"  {label}")
        else:
            value = click.prompt(f"  {label}", default="", show_default=False)

        if value:
            user_input[inp.name] = value

    # Validate
    missing = agent.validate_input(user_input)
    if missing:
        console.print(f"[red]Missing required fields: {', '.join(missing)}[/red]")
        sys.exit(1)

    # Check for API key
    config = Config.from_env()
    errors = config.validate()
    if errors:
        for err in errors:
            console.print(f"[red]{err}[/red]")
        console.print("\n[dim]Set ANTHROPIC_API_KEY to run agents.[/dim]")
        sys.exit(1)

    console.print(f"\n[dim]Running {agent.name}...[/dim]\n")

    runner = AgentRunner(config)
    try:
        result = runner.run(agent, user_input)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    console.print(result.content)
    console.print(f"\n[dim]Model: {result.model} | Tokens: {result.input_tokens}→{result.output_tokens} | {result.latency_ms:.0f}ms[/dim]")

    # Offer scoring
    if click.confirm("\nScore this output for quality?", default=False):
        from tools.scoring import ReadabilityScorer
        from tools.linter import ContentLinter
        from tools.a11y_checker import A11yChecker
        from tools.report import ScoringReport, ReportFormat

        report = ScoringReport(
            text=result.content,
            readability=ReadabilityScorer().score(result.content),
            lint_results=ContentLinter().lint(result.content),
            a11y_result=A11yChecker().check(result.content),
        )
        console.print(f"\n{report.render(ReportFormat.TEXT)}")

    # Offer related agents
    if agent.related_agents:
        console.print(f"\n[bold]Related agents:[/bold] {', '.join(agent.related_agents)}")
        if click.confirm("Hand off to a related agent?", default=False):
            related_name = click.prompt(
                "Which agent?",
                type=click.Choice(agent.related_agents),
            )
            related = registry.get(related_name)
            if related:
                console.print(f"\n[bold cyan]Handing off to: {related.name}[/bold cyan]")
                console.print(f"[dim]Run: cd-agency agent run {related.slug} -i \"{result.content[:50]}...\"[/dim]")


if __name__ == "__main__":
    main()
