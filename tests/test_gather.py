from pathlib import Path

from haunt.capture import RawResult
from haunt.gather import build_evidence, evidence_from_log


def _raw(stderr: str, exit_code: int = 1, signal: int | None = None) -> RawResult:
    return RawResult(
        command=["python", "app.py"],
        cwd=str(Path.cwd()),
        exit_code=exit_code,
        signal=signal,
        duration_s=0.25,
        stdout="out",
        stderr=stderr,
    )


def test_build_evidence_captures_traceback_and_exit():
    stderr = "Traceback (most recent call last):\n  File 'x.py'\nValueError: nope\n"
    evidence = build_evidence(_raw(stderr, exit_code=2), stderr_lines=50)
    assert evidence.exit_code == 2
    assert evidence.traceback is not None
    assert "ValueError" in evidence.traceback
    assert evidence.source == "run"
    assert "python" in evidence.env


def test_tail_limits_lines():
    stderr = "\n".join(f"line{i}" for i in range(200))
    evidence = build_evidence(_raw(stderr), stderr_lines=10)
    assert len(evidence.stderr_tail.splitlines()) == 10
    assert "line199" in evidence.stderr_tail


def test_signal_is_captured():
    evidence = build_evidence(_raw("", exit_code=-9, signal=9), stderr_lines=10)
    assert evidence.signal == 9


def test_evidence_from_log(tmp_path):
    log = tmp_path / "crash.log"
    log.write_text("Traceback (most recent call last):\nKeyError: 'ghost'\n")
    evidence = evidence_from_log(str(log))
    assert evidence.source == "analyze"
    assert evidence.exit_code is None
    assert "KeyError" in evidence.traceback
