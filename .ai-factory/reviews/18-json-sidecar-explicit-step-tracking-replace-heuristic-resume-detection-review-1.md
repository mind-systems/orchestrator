# Code Review: JSON sidecar + explicit step tracking (milestone 18)

**Files reviewed:** `orchestrator/agents.py`, `orchestrator/main.py` (full reads, not just diff)
**Risk level:** 🟢 Low

## Summary

The diff faithfully implements the spec from `.ai-factory/notes/04-explicit-step-tracking.md`:

- `_SESSIONS_RE` removed from `agents.py`; `_read_sessions` / `_write_session` rewritten to use a JSON sidecar at `plan_path.with_suffix('.json')`. `import re` removed cleanly.
- `_detect_milestone_step()` and `_detect_test_milestone_step()` each gained an explicit-step block that runs *after* the canonical-seq resolution and the "plan doesn't exist" early return, and *before* the existing heuristic block. Unrecognized step values correctly fall through to the heuristic.
- `process_milestone()` and `process_test_milestone()` write `step` after every phase per spec. Test-mode mapping correctly diverges (`"implemented"` → `("test_run", 1)`, `"test_run_failed:N"` → `("implement", N+1)`).

The fix for the bug stated in the spec — interrupted `implement` resuming to `review` — works: if `implementer.implement()` raises mid-run, `_write_session(plan_path, "step", "implemented")` is never reached, so `step` remains `"plan_reviewed"` (or a previous `"review_failed:N"`), both of which map to `("implement", …)`. ✅

No blocking issues. The items below are minor robustness notes; none warrant blocking the milestone.

## Findings

### 1. `_read_sessions` will raise on malformed JSON instead of recovering — minor robustness regression

`agents.py:24–28`:

```python
def _read_sessions(plan_path: Path) -> dict[str, str]:
    p = plan_path.with_suffix('.json')
    if not p.exists():
        return {}
    return json.loads(p.read_text())
```

If the sidecar exists but is malformed (e.g. truncated by a `kill -9` between `open()` and final write inside `_write_session`), `json.loads` raises `json.JSONDecodeError` and the whole orchestrator run crashes — without a hint that the cause is the sidecar.

The old regex-based reader was forgiving (no match → `{}`). Since the entire point of this milestone is crash recovery, this is a small reduction in resilience.

**Severity:** low (Python's `write_text` is fast enough that the corruption window is microseconds, and no caller catches the exception).
**Suggestion (optional, not required for PASS):** wrap with `try: json.loads(...) except json.JSONDecodeError: return {}` and log a one-line warning. Not in spec — leave for a follow-up if you ever see it in practice.

### 2. `_write_session` is non-atomic — same crash window

`agents.py:31–35` reads → mutates → writes via `Path.write_text`, which truncates the file then writes. Killing the process between truncate and the final fsync could leave a zero-byte or partial sidecar. Couples with finding #1.

The standard fix is "write to `.tmp` + `os.replace()`". Not in spec — flag only because the spec itself frames this work as crash recovery; if you want belt-and-suspenders, do it as a follow-up.

### 3. Final-iteration failure raises before writing `review_failed:N`

`main.py:267–277` (implement-mode review loop):

```python
else:
    print(f">>> Review found issues — see {review_path}")
    if iteration == max_iterations:
        raise PipelineStopError(...)
    _write_session(plan_path, "step", f"review_failed:{iteration}")
```

When the *last* iteration's review fails, `PipelineStopError` is raised *before* the `step` write. The sidecar retains `step="implemented"` from the start of the iteration. On a future re-run (after the user resolves whatever raised the stop), `_detect_milestone_step()` returns `("review", 1, plan_path)` instead of `("implement", max_iterations+1, …)`.

Consequences:
- The retried review writes `review-1.md`, **overwriting** the failed last-iteration review file (lost history).
- Iteration counter resets to 1 — three more attempts available, which is probably what the user wants on a re-run, but differs from the heuristic-mode behavior (which used `len(review_files) + 1`).

Same pattern in `process_test_milestone()` (`main.py:699–704`) for `test_run_failed`.

**Severity:** low. The PipelineStopError path means the user is intervening anyway; behavior is recoverable; the spec doesn't carve out the max-iteration case either way. Worth a one-line comment in code so a future reader doesn't think it's an oversight, or move the `_write_session` call to *before* the `if iteration == max_iterations:` check so the state is recorded regardless.

### 4. In-flight plans created before this change will lose session state on first resume

A plan that was paused before this commit lands has:
- old HTML comment block (`<!-- orchestrator-sessions -->`) embedded in the `.md`
- no `.json` sidecar

On the next run with the new code:
- `_read_sessions` returns `{}` → `elapsed_offset=0` (wall-clock restarts), `planner`/`implementer` session ids lost (fresh sessions started, `--resume` is not passed)
- `step` is absent → heuristic block runs (same as today, the very behavior we are fixing)

The spec explicitly accepts this ("No backward compat … resume via heuristic fallback"). Calling it out only because the plan-review for this milestone also flagged it (item #7). No action required.

### 5. `int(step_value.split(":")[1])` is fragile if the sidecar is hand-edited

`main.py:108–109` and `main.py:121–122` (and the test-mode equivalents) trust that `plan_review_failed:` / `review_failed:` / `test_run_failed:` are always followed by a parseable integer. The only writers (`f"…:{attempt}"` / `f"…:{iteration}"`) guarantee this, so it's safe today. If somebody ever pokes the sidecar by hand and writes `step: review_failed:foo`, the run crashes with `ValueError`.

**Severity:** trivial. No action needed unless you want defensive parsing in a follow-up.

### 6. `_read_sessions` return type vs. spec signature

Spec §1 wrote `-> dict`; the implementation kept `-> dict[str, str]`. Good call — `main.py` consumers do `int(sessions.get("elapsed", "0"))` and string equality on `step`, so the narrower annotation matches the actual contract. Just noting that the implementation correctly chose to preserve the existing type contract rather than literally copy the spec snippet.

## Positive notes

- The new explicit-step block is placed correctly **after** the canonical-seq resolution (`main.py:77–91`), so a resumed milestone with a renumbered plan still finds its sidecar via the resolved `plan_path`.
- Removal of `import re` is clean — no lingering uses elsewhere in the file.
- Step writes are placed alongside the existing `elapsed` writes wherever the spec suggested, keeping the two checkpoints in sync.
- Test-mode mapping correctly uses `("test_run", 1)` for `"implemented"` and `("implement", N+1)` for `"test_run_failed:N"` — easy place to copy-paste an implement-mode mapping by mistake.
- `process_refactor_milestone` is untouched and now correctly relies on the heuristic fallback (it never writes `step`, so the new explicit-step block is a no-op for it). Verified by inspection of `main.py:288–393`.
- The `step` write after a successful plan (`"planned"`) and after a successful plan review (`"plan_reviewed"`) both occur *before* the loop iterates / breaks, so an interrupt at any "between phases" instant leaves a recoverable state.

## Verdict

The implementation matches the spec and the plan. The bug described in the spec (interrupted-implement → erroneous review) is fixed; the HTML comment is gone from new plan files; refactor mode keeps working via the preserved heuristic. All five tasks landed. Findings #1–#5 are minor and can be addressed as follow-ups if the user wants belt-and-suspenders crash resilience.

REVIEW_PASS
