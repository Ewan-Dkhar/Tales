"""Crash capture: run a process and record how it died."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass


@dataclass
class RawResult:
    command: list[str]
    cwd: str
    exit_code: int
    signal: int | None
    duration_s: float
    stdout: str
    stderr: str


def run_command(command: list[str], cwd: str | None = None) -> RawResult:
    """Run *command*, capturing stdout/stderr and the exit status."""
    if not command:
        raise ValueError("No command provided. Try: haunt run -- python app.py")

    start = time.monotonic()
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
        errors="replace",
    )
    duration = time.monotonic() - start
    exit_code = proc.returncode
    signal_num = -exit_code if exit_code < 0 else None

    return RawResult(
        command=command,
        cwd=cwd or "",
        exit_code=exit_code,
        signal=signal_num,
        duration_s=round(duration, 3),
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )
