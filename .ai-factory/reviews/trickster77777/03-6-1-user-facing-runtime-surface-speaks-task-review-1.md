## Code Review: 6.1 — User-facing runtime surface speaks `task`

**Scope reviewed:** `orchestrator/notify.py`, `orchestrator/main.py`, `orchestrator/runtime.py`, `orchestrator.json.example`, live `orchestrator.json`, and the matching tests (`test_notify.py`, `test_main.py`, `test_config.py`, `test_runtime.py`). Diff read in full against the plan and spec `25-user-facing-runtime-milestone-to-task.md`.

### Verification performed
- **Acceptance grep:** `grep -rn "milestone" orchestrator/*.py tests/*.py` → **zero hits** (also zero case-insensitive). Requirement met.
- **Test suite:** `uv run pytest -q` → **181 passed**. Every renamed assertion, docstring, and the three renamed token-test functions land in lockstep with the source.
- **Live `orchestrator.json` (gitignored, not in diff):** line 8 `telegram_alerts` → `["task-fail", "stop", "done"]` — token renamed correctly. Credentials (`telegram_bot_token`, `telegram_chat_id`) untouched byte-for-byte; `telegram_alerts_example_all` (line 9) deliberately left, exactly per the spec guard. No credential or other-key drift.
- **`orchestrator.json.example`:** `telegram_alerts_example_all` → `["task-fail", "stop", "task", "done"]`; `per_project_override_note` and all credential keys untouched.

### Correctness checks
- **Indivisible slice (§1) is intact:** `_FAIL_ALERTS = {"task-fail"}` (`notify.py:15`), the success call sites emit token `"task"` (`main.py:241,359`), the failure call site emits `"task-fail"` (`main.py:505`), and both config files' token values moved together. The emoji mapping stays coherent: `"task-fail"` → 🔴 (in `_FAIL_ALERTS`), `"stop"` → 🟡, `"task"`/other → 🟢. No partial application, no wrong-emoji or dropped-alert path.
- **No identifier touched:** every change is a string literal or alert token; `state.tasks_done`, `task.title`, `task.slug`, `process_task` etc. (post-5.1 names) are read, not modified. The `runtime.py:39` change alters only the trailing string word, leaving the `state.tasks_done` identifier intact.
- **Out-of-scope tokens preserved:** `"stop"` and `"done"` alert tokens unchanged; `docs/`, prompt bodies, `CLAUDE.md`, `README.md`, `ARCHITECTURE.md` untouched.
- **f-string integrity:** every reworded f-string keeps its interpolations and format args (`{task.title}`, `{seq}-{task.slug}`, `{len(pending)}`, `{total}`, `{_run_summary()}`, `{mins}m {secs}s`) — no placeholder dropped or malformed.

### Notes (non-issues)
- The live `orchestrator.json` does not list the `"task"` success token under `telegram_alerts` (only `task-fail`, `stop`, `done`). This matches pre-change behavior (it previously listed `milestone-fail`, not the success `milestone` token) — an operator routing choice, not a regression introduced here.
- The intentional divergence between the live file's stale `telegram_alerts_example_all` (line 9) and the `.example` is the accepted, spec-sanctioned outcome (live file is gitignored/per-operator; the guard forbids touching that key).

No correctness, security, or runtime concerns found.

REVIEW_PASS
