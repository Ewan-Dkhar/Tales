"""The Narrator Engine: turn evidence into a ghost story with a local model."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from .config import Config
from .models import Evidence
from .prompt import build_messages


def init_sentry(config: Config) -> None:
    if not config.sentry_dsn:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=config.sentry_dsn,
            traces_sample_rate=1.0,
            send_default_pii=False,
        )
    except ImportError:  # pragma: no cover - optional dependency
        pass


@contextmanager
def span(op: str, description: str | None = None) -> Iterator[None]:
    """Start a Sentry span when available; otherwise a no-op."""
    try:
        import sentry_sdk

        with sentry_sdk.start_span(op=op, name=description):
            yield
    except ImportError:  # pragma: no cover - optional dependency
        yield


@contextmanager
def transaction(name: str, op: str = "haunt.pipeline") -> Iterator[None]:
    """Root transaction for the whole pipeline; a no-op without Sentry."""
    try:
        import sentry_sdk

        with sentry_sdk.start_transaction(op=op, name=name):
            yield
    except ImportError:  # pragma: no cover - optional dependency
        yield


def flush_sentry() -> None:
    """Make sure buffered events/spans are sent before a short-lived CLI exits."""
    try:
        import sentry_sdk

        sentry_sdk.flush(timeout=5)
    except ImportError:  # pragma: no cover - optional dependency
        pass


class NarratorEngine:
    def __init__(self, config: Config):
        self.config = config

    def narrate(self, evidence: Evidence) -> Iterator[str]:
        with span("haunt.narrate", f"narrate: {' '.join(evidence.command)}"):
            yield from self._stream(evidence)

    def _stream(self, evidence: Evidence) -> Iterator[str]:
        messages = build_messages(evidence)
        try:
            import ollama
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "The `ollama` package is not installed. Run `uv add ollama`."
            ) from exc

        client = ollama.Client(host=self.config.ollama_host)
        models = [self.config.model]
        if self.config.fallback_model and self.config.fallback_model != self.config.model:
            models.append(self.config.fallback_model)

        last_error: Exception | None = None
        for model in models:
            emitted = False
            try:
                stream = client.chat(
                    model=model,
                    messages=messages,
                    stream=True,
                    options={"temperature": self.config.temperature},
                )
                for chunk in stream:
                    content = _chunk_content(chunk)
                    if content:
                        emitted = True
                        yield content
                return
            except Exception as exc:
                last_error = exc
                if emitted:
                    # Already produced partial text; do not retry into a duplicate story.
                    raise

        raise RuntimeError(
            f"Could not reach the local model. Is Ollama running at "
            f"{self.config.ollama_host} and is `{self.config.model}` pulled?\n"
            f"Try: ollama pull {self.config.model}\n"
            f"Underlying error: {last_error}"
        )


def _chunk_content(chunk: Any) -> str:
    if isinstance(chunk, dict):
        message = chunk.get("message") or {}
        return message.get("content", "") or ""
    message = getattr(chunk, "message", None)
    if message is None:
        return ""
    return getattr(message, "content", "") or ""
