"""Prompt construction for the Ghost Narrator."""

from __future__ import annotations

import json

from .models import Evidence

SYSTEM_PROMPT = """\
You are the Ghost Narrator — a noir detective of crashed processes.

Given forensic evidence about a process's death, write a post-mortem as a ghost story.
Use exactly these sections, each starting with a level-2 Markdown heading:

## The Crash Site
## Last Words
## Prime Suspects
## The Epitaph
## How to Prevent the Haunting

Rules:
- Be vivid and atmospheric, but technically precise.
- Never state facts that are not present in the evidence. If something is unknown, say "unknown".
- Reference concrete evidence (exit code, signal, traceback, commits, files) where it exists.
- Keep each section to at most 6 sentences.
- Do not add any section outside the five above.
"""


def build_messages(evidence: Evidence) -> list[dict[str, str]]:
    payload = json.dumps(evidence.to_dict(), indent=2, default=str)
    user = (
        "Here is the forensic evidence gathered at the scene:\n\n"
        f"```json\n{payload}\n```\n\n"
        "Narrate this death."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
