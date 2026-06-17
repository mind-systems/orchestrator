"""Orchestrator configuration — loaded from orchestrator.json in the project root at startup."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OrchestratorConfig:
    max_iterations: int
    usage_threshold_5h: float
    usage_threshold_weekly: float
    enable_phase_sessions: bool


def load_config() -> OrchestratorConfig:
    """Load and validate config from ~/.orchestrator.json (or ORCHESTRATOR_CONFIG override)."""
    default = Path(__file__).parent.parent / "orchestrator.json"
    path = Path(os.environ.get("ORCHESTRATOR_CONFIG", str(default)))

    if not path.exists():
        raise SystemExit(
            f"Config file not found: {path}\n"
            f"Create it with all required fields:\n"
            f'{{"max_iterations": 3, "usage_threshold_5h": 90, "usage_threshold_weekly": 95, "enable_phase_sessions": true}}'
        )

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise SystemExit(f"Config file is not valid JSON: {path}\n{e}")

    required = ["max_iterations", "usage_threshold_5h", "usage_threshold_weekly", "enable_phase_sessions"]
    for key in required:
        if key not in data:
            raise SystemExit(f"Missing required key '{key}' in {path}")

    return OrchestratorConfig(
        max_iterations=int(data["max_iterations"]),
        usage_threshold_5h=float(data["usage_threshold_5h"]),
        usage_threshold_weekly=float(data["usage_threshold_weekly"]),
        enable_phase_sessions=bool(data["enable_phase_sessions"]),
    )
