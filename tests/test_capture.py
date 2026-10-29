import sys

from haunt.capture import run_command


def test_run_command_captures_exit(tmp_path):
    script = tmp_path / "exit.py"
    script.write_text("import sys; sys.exit(4)\n")
    raw = run_command([sys.executable, str(script)])
    assert raw.exit_code == 4
    assert raw.signal is None


def test_run_command_captures_signal(tmp_path):
    script = tmp_path / "kill.py"
    script.write_text("import os, signal; os.kill(os.getpid(), signal.SIGKILL)\n")
    raw = run_command([sys.executable, str(script)])
    assert raw.exit_code < 0
    assert raw.signal == 9


def test_run_command_requires_command():
    try:
        run_command([])
    except ValueError as exc:
        assert "No command" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")
