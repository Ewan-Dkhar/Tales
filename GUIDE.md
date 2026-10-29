# Using Tales

**Tales** is the project. **`haunt`** is the command it installs: it runs a process, records
what happened when it died, and asks a local open-weight model to narrate the death as a
ghost story.

This guide is the full manual: every command and flag, what gets recorded, how to configure
it, and the things it deliberately does not do.

- [Install](#install)
- [The three ways to feed it a death](#the-three-ways-to-feed-it-a-death)
- [`haunt run`](#haunt-run)
- [`haunt analyze`](#haunt-analyze)
- [`haunt demo`](#haunt-demo)
- [`haunt config`](#haunt-config)
- [Options and exit codes](#options-and-exit-codes)
- [The report](#the-report)
- [What gets collected](#what-gets-collected)
- [Configuration](#configuration)
- [Choosing a model](#choosing-a-model)
- [Sentry tracing](#sentry-tracing)
- [Recipes](#recipes)
- [Troubleshooting](#troubleshooting)
- [How it works](#how-it-works)
- [Limits](#limits)

---

## Install

You need **Python 3.11 or newer** and **Ollama**, running as a separate daemon.

```bash
git clone https://github.com/Ewan-Dkhar/Tales
cd Tales
uv venv
uv pip install -e .
```

`uv pip install -e .` creates the `haunt` entry point inside `.venv/`. Either call it by
path or activate the environment:

```bash
.venv/bin/haunt --help

# or
source .venv/bin/activate
haunt --help
```

With plain `pip`, the same thing works from any environment you like:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

Pull a model once. `gemma2:2b` is the fast one (1.6 GB); `gemma2:9b` is the default and
writes noticeably better prose:

```bash
ollama serve            # if it is not already running
ollama pull gemma2:2b
```

Check that the pieces agree with each other:

```bash
haunt config        # the resolved configuration, as JSON
haunt demo          # a bundled crash, narrated — the whole pipeline in one command
```

And wrap the smallest real thing you can, to see exit-code propagation:

```bash
haunt run -- python -c "raise SystemExit(1)"; echo "exit=$?"   # exit=1
```

---

## The three ways to feed it a death

| Command | Use it when |
|---|---|
| `haunt run -- <cmd>` | The process has not died yet and you want to watch it happen. |
| `haunt analyze <log>` | It already died and you kept the log. |
| `haunt demo` | You want to see the tool work without breaking anything of your own. |

All three funnel into the same contract (`haunt.models.Evidence`), so the narration, the
panels and the report are identical in shape whichever way you got there.

---

## `haunt run`

```bash
haunt run [OPTIONS] -- COMMAND [ARGS...]
```

`haunt` starts `COMMAND`, waits for it to exit, and then gathers the evidence if the process
did not survive. Options belong to `haunt`; everything after `--` belongs to your program.

```bash
haunt run -- python app.py                # narrate the failure
haunt run -- pytest -q tests/             # flags after `--` are passed through
haunt run -m gemma2:2b -- ./bin/worker    # override the model for one run
haunt run -o reports/last-crash.md -- ./job.sh
haunt run --no-narrate -- ./job.sh        # record evidence, do not summon the model
haunt run --exit-zero -- ./job.sh         # always exit 0, whatever happened
```

**Always use `--`.** Without it, `haunt` parses the first arguments itself: a wrapped
program's `-o`, `-m`, `--model`, `--output`, `--no-narrate`, `--exit-zero` or `--help` would
be consumed by `haunt` instead of reaching your program, and anything else fails loudly with
`No such option`. The separator removes the ambiguity completely.

### What happens to the process's output

`stdout` and `stderr` are **captured, not streamed**. Your program's output goes into a pipe
for the evidence, so it does not appear live in the terminal, and the child does not see a
TTY — progress bars, colour and line-buffering behave the way they do when output is piped.
The last `stderr_lines` lines of each stream (default 100) end up in the report.

### Exit codes

`haunt run` is a wrapper, so it exits the way your process did:

| The wrapped process | `haunt run` exits |
|---|---|
| exits `0` | `0` — and nothing is narrated, because nothing died |
| exits `3` | `3` |
| exits `130` | `125` (capped, so it never collides with shell conventions) |
| is killed by `SIGSEGV` | `11` — the signal number |
| could not be started | `127` |
| `haunt` was called with no command | `2` |

`--exit-zero` overrides all of it and forces `0`, which is what `haunt demo` uses so a
demonstration never fails your shell.

### A process that survives

If the command exits cleanly, `haunt` prints `The process survived. Nothing to bury.` and
writes no story and no report — there is no death to narrate, and inventing one would be
exactly the failure mode this tool exists to avoid.

---

## `haunt analyze`

```bash
haunt analyze [OPTIONS] LOGFILE
```

Narrates a death that already happened, from a file you kept. Useful for logs from
containers, CI runs, or a machine you do not want to re-run the crash on.

```bash
docker logs haunted-app > crash.log
haunt analyze crash.log
haunt analyze crash.log -m gemma2:9b -o postmortem.md
haunt analyze crash.log --no-narrate -o evidence.md   # just the evidence appendix
```

What it can and cannot know: the file is the only witness, so `exit_code` and `signal` are
`null`, `duration_s` is `0.0`, and `recent_files` is empty. It still extracts the Python
traceback if there is one, and it still reads the git context of *your current directory*,
which is what makes the narration worth reading.

A missing file exits `2`. Otherwise `analyze` exits `0` — it did not run the process, so it
has no status to report.

`analyze` takes `--model`, `--output` and `--no-narrate`; `--exit-zero` is meaningless here
and does not exist.

---

## `haunt demo`

```bash
haunt demo [OPTIONS]
```

Runs the bundled `haunt/demo_crash.py` with the interpreter that is running `haunt`, and
narrates the resulting `ZeroDivisionError`. It exists so the first thing you see is a real
report, and it always exits `0`.

```bash
haunt demo                     # the default model
haunt demo -m gemma2:2b        # the fast one
haunt demo -o ""               # panels only, no file
```

The demo program crashing is the point; it is not a bug to fix.

---

## `haunt config`

```bash
haunt config
```

Prints the resolved configuration as JSON — defaults merged with `~/.haunt/config.toml` and
the environment — so you can see exactly what a run will use. Note that this includes
`sentry_dsn` if one is configured; do not paste the output into an issue.

`voice` appears in that output but is **not implemented**; it is a placeholder.

---

## Options and exit codes

| Option | Commands | Meaning |
|---|---|---|
| `--model`, `-m` | `run`, `analyze`, `demo` | Any Ollama model tag. Overrides the config for this run. |
| `--output`, `-o` | `run`, `analyze`, `demo` | Where to write the report. `-o ""` writes nothing. |
| `--no-narrate` | `run`, `analyze`, `demo` | Skip the model. The evidence is still collected and still written to `-o`. |
| `--exit-zero` | `run` | Always exit `0`, even if the process failed. |
| `--help` | all | Usage for that command. |

Command-line flags beat environment variables, which beat `~/.haunt/config.toml`, which
beats the built-in defaults.

---

## The report

The report is written to `GHOST_REPORT.md` in the current directory unless `-o` says
otherwise, and it is written **whenever an output path is set** — including when narration
was skipped or the model could not be reached. In that case the story is replaced by one
line, and the evidence is still there:

```markdown
# 👻 Ghost Report

_Summoned by haunt at 2026-10-29T09:26:55.060260+00:00_

_The ghost did not speak. The evidence it was given is recorded below, unchanged._

---

## Raw Evidence

```json
{ ... }
```
```

A full report is the five sections the prompt fixes, then the appendix:

| Section | What it argues from |
|---|---|
| **The Crash Site** | the command, the working directory, the branch, how long it survived |
| **Last Words** | the exit code, any signal, the tail of stdout and stderr |
| **Prime Suspects** | the traceback, the recent commits, the files you changed but never committed |
| **The Epitaph** | one line, quoted back from the evidence |
| **How to Prevent the Haunting** | one concrete change the evidence supports |

Here is a real report from a crash with no traceback at all — `ollama serve` run while the
daemon was already listening (abridged; the report always carries the whole JSON):

```markdown
## Last Words
Its final words echoed through the silent servers: "Error: listen tcp 127.0.0.1:11434:
bind: address already in use." ...

## Raw Evidence
{
  "command": ["ollama", "serve"],
  "exit_code": 1,
  "signal": null,
  "duration_s": 0.015,
  "stderr_tail": "Error: listen tcp 127.0.0.1:11434: bind: address already in use",
  "traceback": null,
  "git": { "branch": "main", "uncommitted": [] },
  "env": { "python": "3.12.5" }
}
```

The prose is a performance. The JSON is testimony. If a sentence in the story is not
supported by the block underneath it, the block is what you trust — and `gemma2:2b` does get
details wrong, which is why the block is there.

`-o ""` skips the file entirely when you only want the panels on screen.

---

## What gets collected

Everything in this table is written into the report and sent to the model. Nothing else is.

| Field | What it holds |
|---|---|
| `command` | the argv you passed; for `analyze`, `["log:<path>"]` |
| `cwd` | the working directory |
| `timestamp` | UTC, ISO 8601 — when the evidence was gathered |
| `exit_code` | the process status; negative when a signal killed it (`-11`), `null` for `analyze` |
| `signal` | POSIX signal number — `11` for `SIGSEGV`; `null` on a normal exit |
| `duration_s` | seconds from a monotonic clock, three decimals; `0.0` for `analyze` |
| `stderr_tail` | the last `stderr_lines` lines — 100 by default |
| `stdout_tail` | the last `stderr_lines` lines — 100 by default |
| `traceback` | `stderr` from the `Traceback` marker onward; `null` when there is none, which is normal for native crashes |
| `git.branch` | `git rev-parse`; `null` outside a repository |
| `git.recent_commits` | `git log --oneline -n 10` |
| `git.diff_stat` | `git diff --stat HEAD` |
| `git.uncommitted` | `git status --porcelain` — the footprints of whoever touched it last |
| `env` | the running interpreter's `python`, `platform` and `cwd`; never the environment variables |
| `recent_files` | files under the working directory modified in the last hour: at most 20, three levels deep, skipping `.git`, `.venv`, `venv`, `node_modules`, `__pycache__`, `.mypy_cache`; empty for `analyze` |
| `source` | `run` or `analyze` |

The git commands run with a five-second timeout and never raise; outside a repository the
whole `git` block is `null` and the narration simply has less to work with.

**Privacy.** The evidence goes to a model running on `localhost` through Ollama. No crash
data leaves the machine unless you configure a Sentry DSN, and even then what is sent is the
trace — operation names and timings — plus any unhandled exception, with PII disabled. The
report is written to your disk in plain text: treat `GHOST_REPORT.md` like a log file,
because it contains file paths, a git diff summary and the last hundred lines your process
printed.

---

## Configuration

Defaults live in code, then `~/.haunt/config.toml`, then environment variables, then flags.

```toml
# ~/.haunt/config.toml
model = "gemma2:9b"
fallback_model = "gemma2:2b"
ollama_host = "http://localhost:11434"
temperature = 0.8
stderr_lines = 100
output = "GHOST_REPORT.md"
# sentry_dsn = "https://<key>@<org>.ingest.sentry.io/<project>"
```

| Key | Default | Environment |
|---|---|---|
| `model` | `gemma2:9b` | `HAUNT_MODEL` |
| `fallback_model` | `gemma2:2b` | `HAUNT_FALLBACK_MODEL` |
| `ollama_host` | `http://localhost:11434` | `HAUNT_OLLAMA_HOST` |
| `temperature` | `0.8` | `HAUNT_TEMPERATURE` |
| `stderr_lines` | `100` | `HAUNT_STDERR_LINES` |
| `output` | `GHOST_REPORT.md` | `HAUNT_OUTPUT` |
| `sentry_dsn` | unset | `SENTRY_DSN` |

`model` and `fallback_model` take any Ollama tag; an empty `fallback_model` disables the
fallback. `temperature` is `0.0`–`2.0`, and lower is more literal. `stderr_lines` must be
`10` or more. An empty `output` writes nothing. `ollama_host` may point at another machine
if you run Ollama remotely.

Out-of-range values are rejected by validation rather than silently clamped, so
`stderr_lines = 5` fails with a Pydantic error naming the field.

Environment variables are handy for a single project without touching your home directory:

```bash
HAUNT_MODEL=gemma2:2b HAUNT_OUTPUT=crash-report.md haunt run -- python app.py
```

---

## Choosing a model

The narrator is just an Ollama chat call, so the model is a configuration value, not a
dependency.

- **`gemma2:2b`** — 1.6 GB, fast enough to feel interactive on a laptop, occasionally wrong
  about details (it once read `return 1 / candles` as "a candle's value was being divided by
  one"). Good for demos and CI.
- **`gemma2:9b`** — the default. Slower, better prose, better at staying inside the evidence.
- **Anything else** — `llama3.1`, `qwen2.5`, a fine-tune, whatever `ollama list` shows.
  `--model` takes the tag verbatim, and nothing else in the tool changes.

`fallback_model` is only tried when the primary model fails **before emitting any text**. If
it fails halfway through, the error propagates instead of splicing two different stories
together.

Because the evidence is serialized before it reaches the model, two different models
narrating the same crash produce different prose over an identical evidence block — apart
from the `timestamp`. The diff comes back with one line changed, and it is the clock:

```bash
haunt analyze crash.log -m gemma2:2b -o fast.md
haunt analyze crash.log -m gemma2:9b -o careful.md
diff fast.md careful.md        # the story differs; the JSON does not
```

---

## Sentry tracing

Tracing is optional and off unless a DSN is configured. The `sentry-sdk` dependency is
installed either way.

```bash
export SENTRY_DSN="https://<key>@<org>.ingest.sentry.io/<project>"
haunt run -- python app.py
```

One transaction per invocation — `haunt.pipeline`, named `haunt run: python app.py` — with
these spans:

| Span | Covers |
|---|---|
| `haunt.capture` | running the wrapped process |
| `haunt.gather` | the traceback, git, environment, recent files |
| `haunt.narrate` | the streaming chat call (the `http.client` span appears underneath it) |
| `haunt.render` | writing the report |

Sampling is `1.0` and `send_default_pii` is `False`: the trace records timing and operation
names, not the evidence itself.

The one ordering rule, if you are reading the source: `init_sentry()` must run **before** the
transaction opens. Initializing it afterwards yields a transaction nobody samples, which
looks exactly like "tracing is broken".

`flush_sentry()` runs before the CLI exits, because a short-lived process would otherwise
drop buffered spans.

---

## Recipes

**Wrap a failing script and keep the report**

```bash
haunt run -- python app.py
# the report lands in ./GHOST_REPORT.md
```

**Record evidence in CI without a model**

Useful on a runner with no Ollama: the evidence is still written, the exit code is still
propagated, and nothing is narrated.

```bash
haunt run --no-narrate -o crash-evidence.md -- ./run-tests.sh
```

**Reproduce a native crash**

```bash
cat > segv.py <<'PY'
import os, signal
os.kill(os.getpid(), signal.SIGSEGV)
PY
haunt run -- python segv.py; echo "exit=$?"   # exit=11, exit_code -11, signal 11
```

There is no traceback in that report. The narration is built from the exit code, the signal
and the last thing the process said — which is the whole point of capturing more than a
stack trace.

**Narrate a log from somewhere else**

```bash
kubectl logs crashy-pod --previous > crash.log
haunt analyze crash.log -o postmortem.md
```

**Keep a shell's exit status while reading the story**

```bash
haunt run --exit-zero -- ./job.sh
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `The ghost did not answer.` | Ollama is not running, or the model is not pulled. | `ollama serve`, then `ollama pull gemma2:2b`. The evidence is still written to `-o`. |
| `Could not start that command.` and exit `127` | The binary does not exist or is not executable. | Check the path. `haunt` uses the same exit code as a shell. |
| `No such option: -c` | The wrapped command's flags were parsed as `haunt`'s. | Put `--` before the command. |
| The wrapped program produced no output in the terminal | Output is captured for evidence, not streamed. | Read the tails in the report, or run the program directly and `haunt analyze` its log. |
| The report is not where you expected | `-o ""` was passed, or the process exited `0`. | A surviving process writes nothing. Use `-o <path>` explicitly. |
| The process exited `0` and nothing happened | That is the design: no death, no story. | |
| `GHOST_REPORT.md` keeps being overwritten | That is the default path. | `-o` per run, or `-o ""` for panels only. |
| A huge log is truncated in the report | Only the last `stderr_lines` lines are kept. | Raise `stderr_lines` in the config. |
| Traces never appear in Sentry | `SENTRY_DSN` unset, or Sentry initialized after the transaction opened. | Set the DSN in the environment or config; keep init before the transaction. |
| Pydantic complains about a config value | `temperature` outside `0–2`, or `stderr_lines` below `10`. | Fix `~/.haunt/config.toml`. |
| `haunt demo` is slow | `gemma2:9b` on a small machine. | `haunt demo -m gemma2:2b`. |

---

## How it works

```
capture.run_command → gather.build_evidence → prompt.build_messages
                    → narrator.NarratorEngine → render.render_story / write_report
```

- **`capture.py`** runs the process and records the exit code, signal, duration and both
  output streams.
- **`gather.py`** fills in the traceback, the git context, the environment fingerprint and
  the recently modified files.
- **`prompt.py`** serializes the evidence into JSON and wraps it in the Ghost Narrator system
  prompt: five fixed headings, no invented facts, the word "unknown" allowed.
- **`narrator.py`** streams the model from Ollama, with the Sentry spans and the fallback
  model.
- **`render.py`** parses the Markdown into Rich panels and writes the report with the
  evidence appendix.

Every stage passes `haunt.models.Evidence` along, which is why the pipeline is testable
without a model: 21 tests, no network, no GPU.

---

## Limits

- **One process, not a tree.** A daemon that spawns children and exits leaves the children
  unobserved.
- **Captured output, not a terminal.** Interactive programs that need a TTY will behave
  differently under `haunt` than under your shell.
- **POSIX exit status.** Signal numbers assume a POSIX system; the project is developed and
  tested on Linux.
- **The model can still be wrong.** The prompt forbids invented facts and the evidence is
  attached, but a small model can misread a line. The appendix is the part you trust.
- **`analyze` is blind to exit codes and durations.** A log is a partial witness.
- **It does not fix your bug.** It points at the line, quotes the evidence, and gets out of
  the way.

---

## Development

```bash
uv pip install -e ".[dev]"
.venv/bin/pytest -q
.venv/bin/ruff check .
```

The landing page in `docs/` is plain HTML and CSS with no build step:

```bash
python3 -m http.server -d docs 8099
```

## License

MIT.
