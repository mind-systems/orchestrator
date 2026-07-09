## Plan Review Summary

**Files Reviewed:** 1 plan against `agents.py`, `notify.py`, `state.py`, `main.py`, `config.py`, and the milestone-07 tests
**Risk Level:** 🟢 Low

### Context Gates
- **Roadmap** (`ROADMAP.md:35`) — the milestone line and its `Spec:` note (`.ai-factory/specs/05-stop-halt-yellow-signal.md`) were followed to the leaf. The plan is a faithful, point-for-point translation of the spec: exception hierarchy, three-tier emoji, `state.py` stash, re-pointed raise sites, manual-stop halts, and `cli()` routing all map 1:1. No divergence. WARN: none.
- **Governing spec** — the spec's "What NOT to do" constraints are all respected: colour is keyed by cause (raise-site migration) not exception class; the generic handler re-raises rather than swallows; docs are untouched (plan `Docs: no`); `milestone`/`done` and the four `milestone` notify calls are left alone.
- **Tests-first (milestone 07)** — `tests/test_notify.py` and `tests/test_main.py` already pin the target behaviour (`halt`→🟡, `RateLimitError`/generic-`Exception`→`halt`, `_check_usage_limits`/resume-past-max→`HaltError`). The plan's implementation choices produce exactly what those red assertions expect, turning them green. `ARCHITECTURE.md`/`RULES.md` gate: no architectural boundary or convention affected.

### Line-reference verification (all confirmed against current source)
- `agents.py:69` `RateLimitError`, `:73` `PipelineStopError`, raise sites `:205,218` — correct.
- `notify.py:24` emoji expression — correct; `_FAIL_ALERTS = {"stop"}` present as stated.
- `main.py:63,67` usage raises; `:357` resume-past-max (implement); `:622` resume-past-max (test) — all four are genuine "nothing judged" halts. Correct to move.
- `main.py:335,350,390,601,615,649,697` — verified each is a real milestone-not-completed failure; correctly left as `PipelineStopError` (🔴).
- `main.py:714-715` graceful-stop print inside `_run_dynamic_loop` (both `config` and `project_dir` in scope); `_handle_sigint` force-quit branch `:22-25`; `run_implement` `:742` / `run_test` `:752`; `cli()` handlers `:783-796` — all accurate.

### Correctness notes
- Handler ordering is sound: `PipelineStopError` and `HaltError` are siblings under `Exception`, `RateLimitError` subclasses `HaltError`. `except PipelineStopError` first, then `except HaltError` (catches `RateLimitError`), then `except Exception` — no shadowing. Deleting the standalone `except RateLimitError` block is safe because the subclass is now caught by the halt handler.
- `SystemExit`/`KeyboardInterrupt` derive from `BaseException`, so the force-quit `sys.exit(1)` and the missing-`ROADMAP_TESTS.md` `sys.exit(1)` pass through `except Exception` untouched — no accidental swallow, single force-quit notify.
- Graceful Ctrl+C emits exactly one `halt` (loop exits normally, no exception reaches `cli()`); double Ctrl+C emits exactly one force-quit `halt` then exits. No double-notification path.
- `is not None` guard on `state.config`/`state.project_dir` correctly protects a signal arriving before `run_*` stashes state. `_run_elapsed()` is module-level in `main.py` and reachable from `_handle_sigint`.

### Positive Notes
- The `TYPE_CHECKING`-only import in `state.py` correctly avoids the `state → config → …` runtime import cycle while keeping the annotations honest.
- Commit dependencies are respected: Task 4 (needs Task 1) lands with/after it; Task 6 (needs Tasks 1, 4) is last; Task 5 (needs Task 3) is grouped in Commit 2.
- The plan explicitly pins the exact notify message strings and alert types, which is what keeps the already-landed tests green.

### Critical Issues
None.

PLAN_REVIEW_PASS
