"""Structured evidence collected about a process's death."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class GitContext:
    """A snapshot of the repository the process died in."""

    branch: str | None = None
    recent_commits: list[str] = field(default_factory=list)
    diff_stat: str = ""
    uncommitted: list[str] = field(default_factory=list)


@dataclass
class Evidence:
    """Everything we know about how a process died."""

    command: list[str]
    cwd: str
    timestamp: str
    exit_code: int | None
    signal: int | None
    duration_s: float
    stderr_tail: str
    stdout_tail: str
    traceback: str | None = None
    git: GitContext | None = None
    env: dict[str, Any] = field(default_factory=dict)
    recent_files: list[str] = field(default_factory=list)
    source: str = "run"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()
