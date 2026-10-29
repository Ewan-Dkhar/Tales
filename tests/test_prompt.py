from haunt.gather import extract_traceback
from haunt.models import Evidence, GitContext
from haunt.prompt import SYSTEM_PROMPT, build_messages


def test_extract_traceback_returns_block():
    stderr = "warning\nTraceback (most recent call last):\n  File 'x.py', line 1\nZeroDivisionError: division by zero\n"
    tb = extract_traceback(stderr)
    assert tb is not None
    assert tb.startswith("Traceback")
    assert "ZeroDivisionError" in tb


def test_extract_traceback_missing():
    assert extract_traceback("no traceback here") is None


def test_build_messages_includes_evidence():
    evidence = Evidence(
        command=["python", "app.py"],
        cwd="/tmp",
        timestamp="2026-10-29T00:00:00Z",
        exit_code=1,
        signal=None,
        duration_s=0.1,
        stderr_tail="boom",
        stdout_tail="",
        git=GitContext(branch="main", recent_commits=["abc init"]),
    )
    messages = build_messages(evidence)
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == SYSTEM_PROMPT
    user = messages[1]["content"]
    assert '"app.py"' in user
    assert "abc init" in user
    assert "boom" in user
