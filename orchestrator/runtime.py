"""Run/signal/process lifecycle — Ctrl+C handling, elapsed-time formatting, sleep prevention."""

from __future__ import annotations

import signal
import subprocess
import sys
import time

from . import state
from .notify import notify
from .agents import kill_active_child


def _handle_sigint(sig, frame):
    if state.stop_requested:
        print("\n>>> Force quit.")
        kill_active_child()
        if state.config is not None and state.project_dir is not None:
            notify(state.config, f"Orchestrator force-quit: {state.project_dir.name}\nRan for {_run_elapsed()}", "halt")
        sys.exit(1)
    state.stop_requested = True
    print("\n>>> Will stop after the current milestone finishes. Press Ctrl+C again to force quit.")


def _fmt_elapsed(seconds: int) -> str:
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours}h {mins}m {secs}s" if hours else f"{mins}m {secs}s"


def _run_elapsed() -> str:
    if state.run_started is None:
        return "unknown"
    return _fmt_elapsed(int(time.monotonic() - state.run_started))


def _with_caffeinate(func, *args, **kwargs):
    """Run a function with macOS sleep prevention (degrades gracefully on non-macOS)."""
    start = time.monotonic()
    try:
        caffeinate = subprocess.Popen(["caffeinate", "-ims"])
    except FileNotFoundError:
        # caffeinate not available (non-macOS); run without sleep prevention
        try:
            func(*args, **kwargs)
        except Exception:
            elapsed = int(time.monotonic() - start)
            print(f">>> Ran for {_fmt_elapsed(elapsed)} before stopping.")
            raise
        return _fmt_elapsed(int(time.monotonic() - start))

    try:
        func(*args, **kwargs)
    except Exception:
        elapsed = int(time.monotonic() - start)
        print(f">>> Ran for {_fmt_elapsed(elapsed)} before stopping.")
        raise
    finally:
        caffeinate.send_signal(signal.SIGTERM)
        caffeinate.wait()

    return _fmt_elapsed(int(time.monotonic() - start))
