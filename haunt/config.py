"""Configuration loading for haunt.

Resolution order (later wins):
  1. built-in defaults
  2. ~/.haunt/config.toml
  3. environment variables (HAUNT_MODEL, HAUNT_OLLAMA_HOST, SENTRY_DSN, ...)
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field

CONFIG_PATH = Path.home() / ".haunt" / "config.toml"


class Config(BaseModel):
    model: str = "gemma2:9b"
    fallback_model: str = "gemma2:2b"
    ollama_host: str = "http://localhost:11434"
    sentry_dsn: str | None = None
    temperature: float = Field(default=0.8, ge=0.0, le=2.0)
    stderr_lines: int = Field(default=100, ge=10)
    output: str = "GHOST_REPORT.md"
    voice: bool = False


def load_config() -> Config:
    data: dict = {}
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("rb") as fh:
            data = tomllib.load(fh)

    env_map = {
        "HAUNT_MODEL": "model",
        "HAUNT_FALLBACK_MODEL": "fallback_model",
        "HAUNT_OLLAMA_HOST": "ollama_host",
        "HAUNT_TEMPERATURE": "temperature",
        "HAUNT_STDERR_LINES": "stderr_lines",
        "HAUNT_OUTPUT": "output",
        "HAUNT_VOICE": "voice",
        "SENTRY_DSN": "sentry_dsn",
    }
    for env_key, field in env_map.items():
        if env_key in os.environ:
            data[field] = os.environ[env_key]

    return Config(**data)
