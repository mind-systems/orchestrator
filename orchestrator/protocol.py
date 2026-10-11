"""The file protocol: sidecar read/write and completion-signal and escalation recognition."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _has_signal(text: str, signal: str) -> bool:
    """Return True if signal appears as an exact line within the last 5 lines."""
    return any(line.strip() == signal for line in text.splitlines()[-5:])


def _has_escalation(text: str) -> bool:
    """Return True if the ESCALATION marker appears as an exact line within the last 5 lines."""
    return _has_signal(text, "ESCALATION")


def _escalation_excerpt(text: str) -> str:
    """Return the first non-empty, non-heading line under a `## Escalation` section.

    Returns "" if the section is absent (placeholder for the sidecar summary)."""
    in_section = False
    for line in text.splitlines():
        if line.strip() == "## Escalation":
            in_section = True
            continue
        if in_section:
            stripped = line.strip()
            if stripped.startswith("#"):
                break
            if stripped:
                return stripped
    return ""


def _read_sessions(plan_path: Path) -> dict[str, str]:
    p = plan_path.with_suffix('.json')
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _write_session(plan_path: Path, key: str, value: str) -> None:
    p = plan_path.with_suffix('.json')
    try:
        data = json.loads(p.read_text()) if p.exists() else {}
    except (json.JSONDecodeError, OSError):
        data = {}
    data[key] = value
    tmp = p.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, p)
