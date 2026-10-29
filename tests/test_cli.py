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
