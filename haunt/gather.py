"""Gather forensic context about a crash."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import time
from pathlib import Path

from .capture import RawResult
from .models import Evidence, GitContext, now_iso

_SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache"}


def _tail(text: str, lines: int) -> str:
    if not text:
        return ""
    return "\n".join(text.splitlines()[-lines:])


def extract_traceback(stderr: str) -> str | None:
    """Return the Python traceback portion of stderr, if present."""
    marker = "Traceback (most recent call last):"
    idx = stderr.find(marker)
    if idx == -1:
        return None
    return stderr[idx:].strip() or None


def _git(args: list[str], cwd: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
            errors="replace",
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def gather_git(cwd: str) -> GitContext | None:
    inside = _git(["rev-parse", "--is-inside-work-tree"], cwd)
    if inside != "true":
        return None
    return GitContext(
        branch=_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd) or None,
        recent_commits=[
            line
            for line in _git(["log", "--oneline", "-n", "10"], cwd).splitlines()
            if line
        ],
        diff_stat=_git(["diff", "--stat", "HEAD"], cwd),
        uncommitted=[
            line
            for line in _git(["status", "--porcelain"], cwd).splitlines()
            if line
        ],
    )


def recent_files(cwd: str, window_s: int = 3600, limit: int = 20) -> list[str]:
    """Files under *cwd* modified in the last *window_s* seconds."""
    root = Path(cwd)
    if not root.is_dir():
        return []
    cutoff = time.time() - window_s
    found: list[tuple[float, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        depth = len(Path(dirpath).relative_to(root).parts)
        if depth >= 3:
            dirnames[:] = []
        for name in filenames:
            path = Path(dirpath) / name
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if mtime >= cutoff:
                found.append((mtime, str(path.relative_to(root))))
    found.sort(reverse=True)
    return [name for _, name in found[:limit]]


def evidence_from_log(path: str, stderr_lines: int = 100) -> Evidence:
    """Build evidence from an existing log file (no live process)."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    cwd = os.getcwd()
    return Evidence(
        command=[f"log:{path}"],
        cwd=cwd,
        timestamp=now_iso(),
        exit_code=None,
        signal=None,
        duration_s=0.0,
        stderr_tail=_tail(text, stderr_lines),
        stdout_tail="",
        traceback=extract_traceback(text),
        git=gather_git(cwd),
        env={"python": sys.version.split()[0], "platform": platform.platform(), "cwd": cwd},
        recent_files=[],
        source="analyze",
    )


def build_evidence(raw: RawResult, stderr_lines: int = 100, source: str = "run") -> Evidence:
    cwd = raw.cwd or os.getcwd()
    return Evidence(
        command=raw.command,
        cwd=cwd,
        timestamp=now_iso(),
        exit_code=raw.exit_code,
        signal=raw.signal,
        duration_s=raw.duration_s,
        stderr_tail=_tail(raw.stderr, stderr_lines),
        stdout_tail=_tail(raw.stdout, stderr_lines),
        traceback=extract_traceback(raw.stderr),
        git=gather_git(cwd),
        env={
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "cwd": cwd,
        },
        recent_files=recent_files(cwd),
        source=source,
    )
