"""Command-line interface for haunt."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from .capture import run_command
from .config import load_config
from .gather import build_evidence, evidence_from_log
from .models import Evidence
from .narrator import NarratorEngine, flush_sentry, init_sentry, span, transaction
from .render import render_story, write_report

app = typer.Typer(
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="Narrate process crashes as ghost stories with a local open-weight model.",
)
console = Console()


def _narrate(evidence: Evidence, config, no_narrate: bool, output: str) -> str | None:
    """Narrate the evidence, render it, and write the report. Returns the story.

    A configured output path always yields a report: when narration is skipped or
    the model cannot be reached, the raw evidence is written on its own.
    """
    text: str | None = None
    if no_narrate:
        console.print("[dim]Narration skipped (--no-narrate).[/dim]")
    else:
        text = _tell_story(evidence, config)

    if output:
        with span("haunt.render", "render report"):
            path = write_report(text, evidence, output)
        console.print(f"\n[dim]Report written to {path}[/dim]")
    return text


def _tell_story(evidence: Evidence, config) -> str | None:
    """Ask the local model for the story and print the panels. None if it stays silent."""
    engine = NarratorEngine(config)
    try:
        with console.status("[magenta]Summoning the ghost…[/magenta]"):
            chunks = list(engine.narrate(evidence))
    except RuntimeError as exc:
        console.print(f"[bold red]The ghost did not answer.[/bold red]\n{exc}")
        return None

    text = "".join(chunks).strip()
    if not text:
        console.print("[bold red]The ghost had nothing to say.[/bold red]")
        return None

    render_story(text, console)
    return text


def _exit_for(evidence: Evidence, force_zero: bool) -> None:
    if force_zero or evidence.exit_code in (0, None):
        raise typer.Exit(code=0)
    raise typer.Exit(code=min(abs(evidence.exit_code), 125) or 1)


@app.command()
def run(
    ctx: typer.Context,
    command: list[str] = typer.Argument(None, help="Command to run, after `--`."),  # noqa: B008
    model: str = typer.Option(None, "--model", "-m", help="Override the model."),
    output: str = typer.Option(None, "--output", "-o", help="Report path (empty to skip)."),
    no_narrate: bool = typer.Option(False, "--no-narrate", help="Capture only, no story."),
    exit_zero: bool = typer.Option(False, "--exit-zero", help="Always exit 0."),
) -> None:
    """Run a command and narrate its death."""
    cmd = list(command) if command else list(ctx.args)
    config = load_config()
    if model:
        config.model = model
    if output is not None:
        config.output = output

    if not cmd:
        console.print(
            "[bold red]No command to run.[/bold red] "
            "Try: haunt run -- python app.py"
        )
        raise typer.Exit(code=2)

    init_sentry(config)
    try:
        with transaction(f"haunt run: {' '.join(cmd)}"):
            with span("haunt.capture", "run command"):
                try:
                    raw = run_command(cmd)
                except OSError as exc:
                    console.print(
                        f"[bold red]Could not start that command.[/bold red]\n{exc}"
                    )
                    raise typer.Exit(code=127) from None
            with span("haunt.gather", "gather evidence"):
                evidence = build_evidence(raw, stderr_lines=config.stderr_lines)
            if evidence.exit_code in (0, None):
                console.print("[dim]The process survived. Nothing to bury.[/dim]")
            else:
                _narrate(evidence, config, no_narrate, config.output)
    finally:
        flush_sentry()
    _exit_for(evidence, exit_zero)


@app.command()
def analyze(
    ctx: typer.Context,
    logfile: str = typer.Argument(..., help="Log file to read."),
    model: str = typer.Option(None, "--model", "-m"),
    output: str = typer.Option(None, "--output", "-o"),
    no_narrate: bool = typer.Option(False, "--no-narrate"),
) -> None:
    """Narrate an existing crash log."""
    config = load_config()
    if model:
        config.model = model
    if output is not None:
        config.output = output

    if not Path(logfile).exists():
        console.print(f"[bold red]No such log file:[/bold red] {logfile}")
        raise typer.Exit(code=2)

    init_sentry(config)
    try:
        with transaction(f"haunt analyze: {logfile}"):
            with span("haunt.gather", "gather evidence"):
                evidence = evidence_from_log(logfile, stderr_lines=config.stderr_lines)
            _narrate(evidence, config, no_narrate or bool(ctx.args), config.output)
    finally:
        flush_sentry()


@app.command()
def demo(
    model: str = typer.Option(None, "--model", "-m"),
    output: str = typer.Option(None, "--output", "-o"),
    no_narrate: bool = typer.Option(False, "--no-narrate"),
) -> None:
    """Run a bundled crashing program and narrate it."""
    config = load_config()
    if model:
        config.model = model
    if output is not None:
        config.output = output

    init_sentry(config)
    try:
        with transaction("haunt demo"):
            with span("haunt.capture", "run demo crash"):
                raw = run_command([sys.executable, "-m", "haunt.demo_crash"])
            with span("haunt.gather", "gather evidence"):
                evidence = build_evidence(raw, stderr_lines=config.stderr_lines)
            _narrate(evidence, config, no_narrate, config.output)
    finally:
        flush_sentry()
    _exit_for(evidence, force_zero=True)


@app.command()
def config() -> None:
    """Show the resolved configuration."""
    console.print_json(load_config().model_dump_json())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
