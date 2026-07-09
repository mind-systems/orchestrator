"""Usage-threshold gating — parse `claude /usage` output and halt if over threshold."""

from __future__ import annotations

import re
import subprocess

from .config import OrchestratorConfig
from .agents import HaltError

SESSION_PATTERN = r"Current session:\s+(\d+(?:\.\d+)?)%"
WEEKLY_PATTERN = r"Current week \(all models\):\s+(\d+(?:\.\d+)?)%"


def _parse_pct(text: str, pattern: str) -> float | None:
    """Return the first captured group of pattern as float, or None if no match."""
    m = re.search(pattern, text)
    return float(m.group(1)) if m else None


def _check_usage_limits(config: OrchestratorConfig) -> None:
    """Run `claude /usage`, log current usage, and stop if either threshold is breached."""
    try:
        result = subprocess.run(["claude", "/usage"], capture_output=True, text=True, timeout=30)
        output = result.stdout
    except Exception:
        print("  [usage check: could not parse output, continuing]")
        return

    session_pct = _parse_pct(output, SESSION_PATTERN)
    weekly_pct = _parse_pct(output, WEEKLY_PATTERN)

    parts = []
    if session_pct is not None:
        parts.append(f"session {session_pct:.0f}%")
    if weekly_pct is not None:
        parts.append(f"week {weekly_pct:.0f}%")
    if parts:
        print(f"  [usage: {' · '.join(parts)}]")
    else:
        print("  [usage check: could not parse output, continuing]")
        return

    session_threshold = config.usage_threshold_5h
    weekly_threshold = config.usage_threshold_weekly

    if session_pct is not None and session_pct >= session_threshold:
        raise HaltError(
            f"Session usage at {session_pct:.0f}% — stopping (threshold: {session_threshold:.0f}%)."
        )
    if weekly_pct is not None and weekly_pct >= weekly_threshold:
        raise HaltError(
            f"Weekly usage at {weekly_pct:.0f}% — stopping (threshold: {weekly_threshold:.0f}%)."
        )
