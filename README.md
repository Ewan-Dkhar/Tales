# 👻 Tales — the Haunted Post-Mortem Narrator

Turn a crash into a ghost story. `haunt` runs your process, gathers the forensic
evidence when it dies, and asks a **local open-weight model** (Gemma by default)
to narrate the post-mortem as a noir ghost story — all offline, all on your machine.

Built for the DEV Hacktoberfest Open-Source AI Challenge: Week 4 ("Ghost in the Machine").

## Install

```bash
uv venv
uv pip install -e .
# or: pip install -e .
```

Pull the default model once:

```bash
ollama pull gemma2:9b    # or gemma2:2b for a fast demo
```

## Use

```bash
haunt run -- python app.py        # wrap a process; narrate if it crashes
haunt run --no-narrate -- ./bin   # capture evidence only
haunt analyze crash.log           # narrate an existing log
haunt demo                        # run a bundled crashing program
haunt config                      # show resolved configuration
```

A report is written to `GHOST_REPORT.md` (override with `-o`).

## How it works

```
Crash Capture → Context Gatherer → Prompt Builder → Narrator Engine → Renderer
   (exit code)   (stderr, git, env)   (evidence JSON)   (Gemma via Ollama)   (Rich + .md)
```

- **Crash Capture** wraps the process and records exit code, signal, duration, and output tails.
- **Context Gatherer** pulls the Python traceback, git branch/commits/diff, env fingerprint, and recently changed files.
- **Prompt Builder** serializes the evidence and instructs the narrator to never invent facts.
- **Narrator Engine** streams Gemma from Ollama, traced with Sentry spans.
- **Renderer** prints Rich panels and writes a Markdown report with a raw-evidence appendix.

## Configuration

`~/.haunt/config.toml`:

```toml
model = "gemma2:9b"
fallback_model = "gemma2:2b"
ollama_host = "http://localhost:11434"
temperature = 0.8
stderr_lines = 100
output = "GHOST_REPORT.md"
# sentry_dsn = "https://..."
```

Environment overrides: `HAUNT_MODEL`, `HAUNT_OLLAMA_HOST`, `HAUNT_TEMPERATURE`,
`HAUNT_OUTPUT`, `SENTRY_DSN`.

## Sentry tracing

Set a DSN to trace the pipeline (`haunt.pipeline` transaction with `capture`, `gather`,
`narrate`, and `render` spans). Without a DSN the tracing path is a no-op.

```bash
export SENTRY_DSN="https://<key>@<org>.ingest.sentry.io/<project>"
# or add `sentry_dsn = "..."` to ~/.haunt/config.toml
```

## Landing page

The site in `docs/` is plain static HTML, CSS and a little JavaScript — no build step.
Served by GitHub Pages from `main` at `https://ewan-dkhar.github.io/Tales/`.

```bash
python3 -m http.server -d docs 8099   # preview locally
```

`docs/index.html` uses a marginalia layout: the left margin carries the timeline of the
demo run, the column carries the argument, and the two-ink comparison sets recorded
evidence in mono against narrated prose in serif. The hero line is the model's actual
first sentence about the bundled demo crash.

## Development

```bash
uv pip install -e ".[dev]"
pytest
ruff check .
```

## License

MIT
