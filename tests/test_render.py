from haunt.models import Evidence
from haunt.render import build_report_markdown, parse_sections


def _evidence() -> Evidence:
    return Evidence(
        command=["python", "app.py"],
        cwd="/tmp",
        timestamp="2026-10-29T00:00:00Z",
        exit_code=1,
        signal=None,
        duration_s=0.1,
        stderr_tail="boom",
        stdout_tail="",
    )


def test_parse_sections():
    text = "## The Crash Site\nIt died.\n\n## Last Words\nboom\n"
    sections = parse_sections(text)
    assert [h for h, _ in sections] == ["The Crash Site", "Last Words"]
    assert sections[0][1] == "It died."


def test_parse_sections_without_headings_wraps():
    sections = parse_sections("just a story")
    assert sections == [("The Haunting", "just a story")]


def test_report_has_evidence_appendix():
    report = build_report_markdown("## The Crash Site\nIt died.", _evidence())
    assert "# 👻 Ghost Report" in report
    assert "## Raw Evidence" in report
    assert '"exit_code": 1' in report
