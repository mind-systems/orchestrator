# Code Review (Re-review) — Yellow `halt` alert (milestone 10)

**Files reviewed:** `orchestrator/agents.py`, `orchestrator/notify.py`, `orchestrator/state.py`, `orchestrator/main.py`, against plan `.ai-factory/plans/10-...md` and spec `.ai-factory/specs/05-stop-halt-yellow-signal.md`.
**Test suite:** `uv run pytest` — 78 passed.

## Verdicts on previous findings (review-1)

### 1. `RateLimitError` unused import in `main.py` — **Fixed**

Review-1 flagged that deleting the `except RateLimitError` block orphaned the import at `main.py:13`.

Current content of `main.py:13`:
```python
from .agents import HaltError, Implementer, PipelineStopError, PlannerReviewer, PlanReviewer, TestRunner, _read_sessions, _write_session, kill_active_child
```
`RateLimitError` is no longer imported, and a full-file grep for `RateLimitError` in `main.py` returns no matches. The name is still defined and raised in `agents.py`, where it is caught in `cli()` via its `HaltError` base — so removing the import changes no behaviour. **Fixed.**

## Fresh full review

Re-read all four changed files in full and re-verified the runtime-critical paths:

- **Exception hierarchy** (`agents.py:69-74`): `HaltError(Exception)` precedes `RateLimitError(HaltError)`; `PipelineStopError(Exception)` remains a sibling. Raise sites `agents.py:205,218` untouched.
- **Emoji tiers** (`notify.py:24`): `🔴 / 🟡 / 🟢` precedence correct; `halt` still gated by `telegram_alerts` membership.
- **State stash** (`state.py`, `main.py:747-748,760-761`): `config`/`project_dir` declared under a `TYPE_CHECKING`-only import (no runtime cycle) and set as the first statements of `run_implement`/`run_test` before the signal handler registers.
- **Raise migration** (`main.py`): exactly the four operational halts moved to `HaltError` (usage `:65,69`; resume-past-max `:359,624`); the seven milestone-not-completed raises stay `PipelineStopError`.
- **Manual-stop alerts**: graceful (`main.py:718`) fires one `halt` on normal loop exit; force-quit (`main.py:25-26`) fires one `halt` guarded by `is not None`, then `sys.exit(1)` (a `BaseException`) bypasses `except Exception`.
- **`cli()` routing** (`main.py:790-810`): order `PipelineStopError` → `HaltError` (catches `RateLimitError`) → `Exception` is non-shadowing; the generic handler alerts then bare-`raise`s (traceback + non-zero exit survive) with an empty-message guard `if str(e) else ''`. The `HaltError` handler's unguarded `str(e).splitlines()[0]` is safe because every `HaltError` source carries a non-empty message.
- **`_with_caffeinate`** does not swallow `HaltError`/`PipelineStopError`, and its `finally` still tears down caffeinate on force-quit `SystemExit`.

No new correctness, security, or runtime issues found. The fix was surgical (single import-line change) and introduced nothing else.

REVIEW_PASS
