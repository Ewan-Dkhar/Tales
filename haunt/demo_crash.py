"""A small program that dies so `haunt demo` has something to narrate."""

from __future__ import annotations

import sys


def summon_ghost() -> float:
    candles = 0
    print("Lighting the candles...", file=sys.stderr)
    print("The room grows cold.", file=sys.stderr)
    return 1 / candles


if __name__ == "__main__":
    summon_ghost()
