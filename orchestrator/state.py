"""Shared mutable state for the orchestrator process."""
from __future__ import annotations

import subprocess

stop_requested: bool = False
active_proc: subprocess.Popen | None = None
run_started: float | None = None
