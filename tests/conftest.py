import pytest


@pytest.fixture(autouse=True)
def _hermetic_config(monkeypatch):
    """Keep tests off the network and away from the user's real Sentry project."""
    monkeypatch.setenv("SENTRY_DSN", "")
    monkeypatch.setenv("HAUNT_MODEL", "gemma2:2b")
