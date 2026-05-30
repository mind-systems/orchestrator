# Plan Review: Sidecar robustness — three follow-up fixes

**Plan file:** `plans/19-sidecar-robustness-three-follow-up-fixes.md`
**Risk Level:** 🟢 Low

## Context Gates

- **ARCHITECTURE.md:** not present in `.ai-factory/` (only `DESCRIPTION.md`, `ROADMAP.md`, `notes/`). No alignment violations to flag — WARN: optional file absent.
- **RULES.md:** not present. WARN: optional file absent. Project-level conventions from root `CLAUDE.md` (no test suite, file-based agent communication) are respected by the plan.
- **ROADMAP.md:** Milestone is the unchecked item on line 51 of `ROADMAP.md`. Plan title matches the milestone heading. The plan correctly references the spec note at `.ai-factory/notes/05-sidecar-robustness.md`. ✓

## Codebase Verification

All file paths and line references in the plan check out against the current tree:

- `_read_sessions` is at `agents.py:24-28` ✓ (matches plan)
- `_write_session` is at `agents.py:31-35` ✓
- `os` is already imported at `agents.py:6` ✓ (Fix 3 needs no new imports)
- `process_milestone()` is at `main.py:149`, review-loop failure block at `main.py:270-277` ✓
- `process_test_milestone()` is at `main.py:577`, test-loop failure block at `main.py:694-704` ✓
- The bridge patch write is at `main.py:697-698` ✓ (plan correctly preserves it)
- `_write_session` is imported into `main.py:13` ✓
- `_detect_milestone_step` honors `review_failed:N` at `main.py:110-112` and `test_run_failed:N` at `main.py:544` ✓ — confirms Fix 2 will achieve its stated routing effect

## Scope Correction — Correct Catch

The milestone description in `ROADMAP.md:51` says **"All three in `agents.py` only"** and the spec note (`notes/05-sidecar-robustness.md`) repeats that claim. **Both are wrong** — Fix 2 must touch `main.py` because that is where `process_milestone()` and `process_test_milestone()` live; `agents.py` only exposes the `_write_session` helper. The plan's "Scope correction" box at the top is exactly right to flag this. No drift.

## Critical Issues

None blocking. All three fixes are technically correct as specified:

- Fix 1: `try/except (json.JSONDecodeError, OSError)` returning `{}` cleanly restores the pre-sidecar fault-tolerant semantics.
- Fix 2: Moving `_write_session(..., "step", f"review_failed:{iteration}")` (and the test-loop twin) above the `if iteration == max_iterations: raise` guard does fix the next-run resume routing.
- Fix 3: `tmp.write_text(...) + os.replace(tmp, p)` is the standard atomic-rename idiom and is safe on POSIX and Windows.

## Concerns Worth Noting (non-blocking)

### 1. `_write_session`'s own internal read remains unprotected

After Fix 3, `_write_session` still does an unguarded `json.loads(p.read_text()) if p.exists() else {}` on its first line. Fix 1 only protects `_read_sessions`. If the sidecar somehow ends up corrupt (legacy file, manual edit, partial state from before this milestone deploys, parallel non-orchestrator process), the **next `_write_session` call will crash with `JSONDecodeError`** — defeating Fix 1's robustness guarantee from the writer's side.

The plan's Task 2 note explicitly defers this ("Do not alter semantics beyond the atomic-replace pattern"), which is a defensible scope choice — Fix 3 eliminates the *new* corruption window, and Fix 1 covers the *read* path that resume relies on. But it leaves a residual crash mode: a process that boots with an already-corrupt sidecar (e.g. left over from a pre-Fix-3 `kill -9`) will read fine via `_read_sessions` and then crash the first time it tries to write a step update.

Suggested low-risk addition (one line, same try/except family):

```python
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
```

Not a blocker — flag for the implementer to consider, or accept the deferral as documented.

### 2. Resume after `PipelineStopError` with unchanged `max_iterations`

Fix 2 makes the sidecar record `review_failed:N` so the next run routes to `("implement", N+1, plan_path)`. But if the previous run hit `max_iterations` (default 3), then on resume `impl_start = N+1 = 4` while `max_iterations + 1 = 4`, so the implement/review `for` loop body **never executes**. The function then falls straight through to `mark_done(...)` + `_git_commit(...)` — i.e. the orchestrator would commit broken code marked as "done."

The plan does not address this. It is arguably out of scope (the user is expected to bump `ORCHESTRATOR_MAX_ITERATIONS` before resuming) and the same risk exists today via the pre-existing `review_failed:N` writes from non-final iterations. But it is now surfaced more directly by this change: previously the sidecar said `"implemented"` after a max-out, which at least restarted iteration 1 (overwriting `review-1.md`, the original bug) — buggy, but at least it *tried again*. After this fix, the buggy overwrite is gone but is replaced by a silent skip-to-commit.

Recommended (not required to land this milestone): the implementer or a follow-up milestone should add a guard at the top of the implement/review loop so `impl_start > max_iterations` raises rather than falling through to `mark_done`. Worth a one-line spec note for next time; do not block on it here.

### 3. Leftover `.json.tmp` files

`os.replace` always succeeds in cleaning up the tmp on the happy path, but if the process is `kill -9`'d between `tmp.write_text(...)` and `os.replace(...)`, a sibling `*.json.tmp` is left in `plans/`. It is harmless (not read by anything, not committed if `.gitignore` excludes it, overwritten on next call), but worth being aware of. No action required.

## Positive Notes

- The plan's "Scope correction" callout catches a real discrepancy between the milestone description and the actual file layout — this is exactly what a plan should do when the input is wrong.
- Target code snippets are concrete and copy-pasteable; the implementer will not have to guess.
- Verification section honors the project convention ("no test suite or linter is configured" per `CLAUDE.md`) by specifying inspection-only checks — appropriate for this codebase.
- Single-commit plan is right-sized for three small, tightly-related fixes; no over-engineering.
- The note about preserving the bridge patch write at `main.py:697-698` (Task 4) shows the planner read the surrounding code carefully and is not blindly moving a block.

PLAN_REVIEW_PASS
