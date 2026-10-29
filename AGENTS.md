# Tales — Haunted Post-Mortem Narrator

A Python CLI (`haunt`) that runs a process, gathers crash evidence, and narrates the death as a ghost story using a local open-weight model (Gemma via Ollama). Built for DEV Hacktoberfest Open-Source AI Challenge: Week 4 ("Ghost in the Machine"), tag `#hf26challenge`.

## Setup

```bash
uv venv
uv pip install -e ".[dev]"
ollama serve
ollama pull gemma2:2b        # fast demo model; default config uses gemma2:9b
```

## Commands

```bash
.venv/bin/haunt run --no-narrate -- python app.py   # capture only
.venv/bin/haunt run -- python app.py                # capture + narrate
.venv/bin/haunt analyze crash.log
.venv/bin/haunt demo
.venv/bin/haunt config
```

- Always pass the wrapped command after `--`. Without it, Click rejects flags like `-c` as unknown options.
- The report defaults to `GHOST_REPORT.md`; use `-o ""` to skip writing it.
- `haunt run` propagates the wrapped process's exit code; `haunt demo` always exits 0.
- When Ollama is unreachable, `_narrate` prints a friendly error and returns; it does not crash the CLI.

## Verify

```bash
.venv/bin/pytest -q
.venv/bin/ruff check .
```

Run both before claiming a change is complete.

## Architecture

`haunt/cli.py` is the only entrypoint; it wires the pipeline and is the place to add flags.
Flow: `capture.run_command` → `gather.build_evidence` → `prompt.build_messages` → `narrator.NarratorEngine.narrate` (streams Gemma) → `render.render_story` + `render.write_report`.

- `models.Evidence` is the single data contract passed between stages. Add fields there and in `gather`, not ad hoc dicts.
- `narrator.span()` is a no-op unless `SENTRY_DSN` is set. Do not assume a Sentry hub exists.
- Prompt must forbid invented facts; keep the raw-evidence appendix in `render.build_report_markdown`.
- `demo_crash.py` is intentionally a crashing module used by `haunt demo`; do not "fix" the division by zero.

## Config

`~/.haunt/config.toml` or env vars (`HAUNT_MODEL`, `HAUNT_OLLAMA_HOST`, `HAUNT_TEMPERATURE`, `HAUNT_OUTPUT`, `SENTRY_DSN`). Pydantic model in `haunt/config.py`; CLI flags override loaded config.

## Gotchas

- `uv venv` uses managed CPython 3.12 (not the system 3.14) — use `.venv/bin/...` explicitly.
- On native crash/signal, `stderr` may be empty; the report still renders from exit code + signal.
- `ollama` server must be running separately; the package alone is not enough.
