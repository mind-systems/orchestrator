# Plan: 29.2 — the file protocol lives in `protocol.py`

## Context
Move the file protocol out of `orchestrator/agents.py` into a new vocabulary module, `orchestrator/protocol.py`. The protocol is the sidecar helpers `_read_sessions` and `_write_session` and the recognition helpers `_has_signal`, `_has_escalation` and `_escalation_excerpt`. After the move, `main` and `resume` no longer import `agents` for the protocol. `.ai-factory/ARCHITECTURE.md` § Dependency Rules places `protocol.py` in the Vocabulary layer, which imports nothing from the package at runtime. The task spec is `.ai-factory/specs/trickster77777/0069-the-file-protocol-lives-in-protocol.md`. The change is behaviour-neutral and adds no test.

Ground truth checked: no test patches or `getattr`s these five names on `agents`. `tests/test_agents.py` imports them by name and uses real files under `tmp_path`. `agents.py` still uses `json` (stream-json parsing in `_run_claude`) and `os` (`kill_active_child`, the `_run_claude` env) after the move, so both of its imports stay.

## Settings
- Testing: no (the existing suite must stay green: `uv run pytest`)
- Logging: none
- Docs: no

## Tasks

### Move the protocol

- [x] **Create `orchestrator/protocol.py`**
  Files: `orchestrator/protocol.py`
  Follow the shape of `orchestrator/errors.py`. Add a one-line module docstring naming the concern: the file protocol, meaning sidecar read/write and completion-signal and escalation recognition. Then add `from __future__ import annotations`, and the stdlib imports `json`, `os` and `from pathlib import Path`. Move these five functions from `orchestrator/agents.py` exactly as they are, with signatures, bodies and docstrings character-for-character (including the `'.json'` / `'.json.tmp'` quoting) and in the same order: `_has_signal`, `_has_escalation`, `_escalation_excerpt`, `_read_sessions`, `_write_session`. The module imports nothing from the `orchestrator` package.

- [x] **Remove the helpers from `agents.py` and import them from `protocol`** (depends on Create `orchestrator/protocol.py`)
  Files: `orchestrator/agents.py`
  Delete the five function definitions. They sit after `MAX_RETRIES` / `RETRY_DELAY` and before `_is_overloaded`. Keep `MAX_RETRIES` and `RETRY_DELAY` where they are, with normal blank-line spacing before `_is_overloaded`. Add `from .protocol import _escalation_excerpt, _has_escalation, _has_signal, _write_session` beside the existing `from .errors import …` line. The roles use these four names: `PlannerReviewer.plan`/`.review`, `PlanReviewer.review_plan` and `Implementer.implement`. `_read_sessions` is not used in `agents.py`, so do not import it; grep to confirm. Re-export nothing: no extra names, no `__all__`, no alias. Keep `import json` and `import os`, because they are still used.

- [x] **Point `main.py` and `resume.py` at `protocol`** (depends on Create `orchestrator/protocol.py`)
  Files: `orchestrator/main.py`, `orchestrator/resume.py`
  - `main.py`: remove `_read_sessions` and `_write_session` from the `from .agents import …` line, and keep the rest of that line (`REVIEW_VERIFY`, `TEST_RUN_VERIFY`, `Implementer`, `PlannerReviewer`, `PlanReviewer`, `VerifyKind`) unchanged. Add `from .protocol import _read_sessions, _write_session` in the import block, following its existing ordering style.
  - `resume.py`: change `from .agents import REVIEW_VERIFY, TEST_RUN_VERIFY, VerifyKind, _read_sessions` to `from .agents import REVIEW_VERIFY, TEST_RUN_VERIFY, VerifyKind`, and add `from .protocol import _read_sessions`. The remaining `agents` edge from `resume` belongs to task 29.3 and stays as it is here.

### Update the tests

- [x] **Import the protocol helpers from `protocol` in `tests/test_agents.py`** (depends on Remove the helpers from `agents.py`)
  Files: `tests/test_agents.py`
  Remove `_escalation_excerpt`, `_has_escalation`, `_has_signal`, `_read_sessions` and `_write_session` from the `from orchestrator.agents import (…)` block. Add `from orchestrator.protocol import _escalation_excerpt, _has_escalation, _has_signal, _read_sessions, _write_session` next to the `from orchestrator.errors import …` line. Leave the test bodies untouched. The module docstring lists what the file covers and names no module, so it stays as it is.

- [x] **Verify** (depends on all above)
  Run `uv run pytest`. The suite must pass with no test changed beyond the imports. Then run `grep -n "_read_sessions\|_write_session\|_has_signal\|_has_escalation\|_escalation_excerpt" orchestrator/*.py` and confirm two things: the five `def`s appear only in `protocol.py`, and every other hit is a use or a `from .protocol import`. Finally, confirm that `protocol.py` has no `from .` / `from orchestrator` import.
