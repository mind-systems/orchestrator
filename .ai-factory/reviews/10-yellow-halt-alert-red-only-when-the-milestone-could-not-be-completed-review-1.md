# Code Review — Yellow `halt` alert (milestone 10)

**Files reviewed:** `orchestrator/agents.py`, `orchestrator/notify.py`, `orchestrator/state.py`, `orchestrator/main.py` (in full), against spec `.ai-factory/specs/05-stop-halt-yellow-signal.md` and the tests-first milestone (`tests/test_notify.py`, `tests/test_main.py`).
**Test suite:** `uv run pytest` — 78 passed.

## What was verified correct

- **Exception hierarchy** (`agents.py:69-74`): `HaltError(Exception)` defined before `RateLimitError(HaltError)`; `PipelineStopError(Exception)` left as a sibling. The two `raise RateLimitError(...)` sites (`agents.py:205,218`) are untouched.
- **Three-tier emoji** (`notify.py`): `_HALT_ALERTS = {"halt"}` added; the pick is `🔴 / 🟡 / 🟢` in the right precedence; gating via `telegram_alerts` membership is unchanged.
- **State stash** (`state.py`, `main.py:745-746,758-759`): `config`/`project_dir` declared under a `TYPE_CHECKING`-only import (no runtime cycle), and set as the first statements of both `run_implement`/`run_test` before `signal.signal(...)` registers the handler.
- **Raise-site migration** (`main.py`): exactly the four operational halts moved to `HaltError` — usage session/weekly (`:65,69`) and resume-past-max implement/test (`:359,624`). The seven genuine milestone-not-completed raises (`:337,352,392,603,617,651,699`) correctly stay `PipelineStopError`. Confirmed by full grep of the file.
- **Manual-stop alerts** (`main.py:718` graceful, `:25-26` force-quit): graceful stop notifies exactly once (loop exits normally, no exception reaches `cli()`); force-quit `sys.exit(1)` raises `SystemExit` (a `BaseException`) which skips the graceful block and is not caught by `except Exception`, so exactly one force-quit notify fires. The `is not None` guard protects a signal arriving before state is stashed.
- **`cli()` routing** (`main.py:790-810`): handler order `PipelineStopError` → `HaltError` (catches `RateLimitError` subclass) → `Exception` is non-shadowing and correct. The generic handler alerts `halt` then bare-`raise`s, so the traceback and non-zero exit survive; its `str(e).splitlines()[0] if str(e) else ''` guard is empty-message-safe.
- **`_with_caffeinate`** (`main.py:420-445`): its `except Exception` does not swallow `HaltError`/`PipelineStopError` (both re-raise); on force-quit `SystemExit` the `finally` still tears down the caffeinate child before propagation.
- **Empty-message safety of the halt handler** (`main.py:801` unguarded `str(e).splitlines()[0]`): every `HaltError` source carries a non-empty message (usage strings, resume-past-max string, `RateLimitError(result_text)` where `result_text` provably contains "hit your limit"/"resets"), so no `IndexError`. Mirrors the pre-existing `PipelineStopError` handler.

## Findings

### 1. `RateLimitError` is now an unused import in `main.py` (low)

`main.py:13` still imports `RateLimitError`, but Task 6 deleted the only reference — the standalone `except RateLimitError` block. A grep confirms the name now appears only on the import line (count: 1). It is dead code introduced by this diff.

- **Impact:** none at runtime (no linter is configured), purely cleanliness. `RateLimitError` is caught via its `HaltError` base, so removing the import does not change behaviour.
- **Fix:** drop `RateLimitError` from the `from .agents import ...` list at `main.py:13`.

This is in-scope (the diff orphaned it), not a deferred observation.

## Verdict

One low-severity cleanup finding; no correctness, security, or runtime-breaking issues. The implementation is a faithful, test-green translation of the spec.
