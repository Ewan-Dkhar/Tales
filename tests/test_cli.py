from typer.testing import CliRunner

from haunt.cli import app

runner = CliRunner()


def test_config_command():
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "gemma2" in result.output


def test_run_no_narrate_propagates_failure(tmp_path):
    script = tmp_path / "boom.py"
    script.write_text("raise SystemExit(3)\n")
    result = runner.invoke(
        app,
        ["run", "--no-narrate", "--", "python", str(script)],
    )
    assert result.exit_code == 3
    assert "Narration skipped" in result.output


def test_analyze_missing_file():
    result = runner.invoke(app, ["analyze", "does-not-exist.log"])
    assert result.exit_code == 2


def test_run_without_command_exits_two():
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 2
    assert "No command to run" in result.output


def test_run_missing_binary_exits_127():
    result = runner.invoke(app, ["run", "--no-narrate", "--", "haunt-no-such-binary"])
    assert result.exit_code == 127
    assert "Could not start that command" in result.output


def test_run_survived_writes_no_report(tmp_path):
    report = tmp_path / "report.md"
    result = runner.invoke(app, ["run", "-o", str(report), "--", "python", "-c", "pass"])
    assert result.exit_code == 0
    assert "The process survived" in result.output
    assert not report.exists()


def test_no_narrate_still_writes_evidence(tmp_path):
    script = tmp_path / "boom.py"
    script.write_text("raise SystemExit(3)\n")
    report = tmp_path / "evidence.md"
    result = runner.invoke(
        app,
        ["run", "--no-narrate", "-o", str(report), "--", "python", str(script)],
    )
    assert result.exit_code == 3
    text = report.read_text()
    assert "Narration skipped" in result.output
    assert "## Raw Evidence" in text
    assert '"exit_code": 3' in text
    assert "The ghost did not speak" in text
