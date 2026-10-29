"""Render the ghost story to the terminal and to disk."""

from __future__ import annotations

import json
import re
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .models import Evidence

_SECTION_RE = re.compile(r"(?m)^##\s+(.+)$")


def parse_sections(text: str) -> list[tuple[str, str]]:
    """Split Markdown into (heading, body) pairs on level-2 headings."""
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        body = text.strip()
        return [("The Haunting", body)] if body else []

    sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((match.group(1).strip(), text[start:end].strip()))
    return sections


def render_story(text: str, console: Console | None = None) -> None:
    console = console or Console()
    sections = parse_sections(text)
    if not sections:
        console.print("[dim]The ghost had nothing to say.[/dim]")
        return
    for heading, body in sections:
        console.print(
            Panel(
                Markdown(body or "_…silence…_"),
                title=f"👻 {heading}",
                border_style="magenta",
                padding=(0, 1),
            )
        )


def build_report_markdown(text: str, evidence: Evidence) -> str:
    appendix = json.dumps(evidence.to_dict(), indent=2, default=str)
    return (
        "# 👻 Ghost Report\n\n"
        f"_Summoned by haunt at {evidence.timestamp}_\n\n"
        f"{text.strip()}\n\n"
        "---\n\n"
        "## Raw Evidence\n\n"
        "```json\n"
        f"{appendix}\n"
        "```\n"
    )


def write_report(text: str, evidence: Evidence, path: str | Path) -> Path:
    out = Path(path)
    out.write_text(build_report_markdown(text, evidence), encoding="utf-8")
    return out
