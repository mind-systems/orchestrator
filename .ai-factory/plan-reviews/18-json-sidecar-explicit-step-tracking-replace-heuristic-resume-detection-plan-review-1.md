# Plan Review: JSON sidecar + explicit step tracking

**Files Reviewed:** 1 plan + 1 spec + agents.py + main.py
**Risk Level:** 🟢 Low

## Context Gates

- **Architecture gate:** WARN — `.ai-factory/ARCHITECTURE.md` not present in this project. No boundary checks performed.
- **Rules gate:** WARN — `.ai-factory/RULES.md` not present. No explicit convention violations checkable.
- **Roadmap gate:** OK — milestone exists in `.ai-factory/ROADMAP.md` (this is `feat`-shaped work; linkage is implicit via the plan slug `18-json-sidecar-explicit-step-tracking-replace-heuristic-resume-detection.md`).

## Critical Issues

None — no blockers identified.

## Issues / Clarifications

### 1. Ambiguous wording for `"plan_reviewed"` write location (Task 2)

Task 2 says:
> When `plan_passed` is True (after `break` at line 207) → `"plan_reviewed"`.

You cannot place a statement after `break` in the same scope. The current code at lines 205–207 is:

```python
if plan_passed:
    print(f">>> Plan review passed — see {plan_review_path}")
    break
```

Two viable placements; the plan should pick one:

- (a) Inside the `if plan_passed:` block **before** the `break`:
  ```python
  if plan_passed:
      print(f">>> Plan review passed — see {plan_review_path}")
      _write_session(plan_path, "step", "plan_reviewed")
      break
  ```
- (b) After the `for attempt in …:` loop (because the only non-raise exit is via `plan_passed=True`):
  ```python
  for attempt in range(counter, max_iterations + 1):
      …
  # plan review passed (else PipelineStopError was raised inside)
  _write_session(plan_path, "step", "plan_reviewed")
  ```

Option (a) is closer to the spec's "alongside the existing elapsed write" pattern and is recommended. Please make this explicit in the plan so the implementer doesn't guess.

The same clarification is needed for Task 4 (test mode) — the plan only says "on pass → `"plan_reviewed"`" without naming a line.

### 2. No `step` write after successful review (minor inefficiency)

The spec §2 transition table has no row for "review passes" (only "review fails"). After a successful review at iteration N, the sidecar still holds `step="implemented"` (or `"review_failed:K"` from the previous iteration), the loop breaks, then `mark_done` + `_git_commit` runs.

If the process is killed in the narrow window after review pass but before `mark_done`/commit, the milestone is still pending in the roadmap on resume. `_detect_milestone_step` would read `step="implemented"` → `("review", 1, plan_path)` → re-run review. That's correct but wastes one review pass.

Same issue applies to `process_test_milestone` (would re-run tests).

This is acceptable per the spec, but the plan should either:
- explicitly note "we accept one possibly-redundant review on this rare crash window", or
- add a `_write_session(plan_path, "step", "reviewed")` (or `"done"`) just before `mark_done(...)`, plus the corresponding mapping in `_detect_milestone_step` (`"reviewed"`/`"done"` → `("done", 0, plan_path)`).

Either is fine — but right now the plan is silent and the implementer will make a different choice than the reviewer.

### 3. No `step` write after a successful plan revision (minor inefficiency)

In `process_milestone()` lines 215–219, after `_write_session(plan_path, "step", f"plan_review_failed:{attempt}")` (Task 2's new write) and the subsequent `planner_reviewer.plan(...)` revision, no step is written. If killed between the revision completing and the next `review_plan()` starting, sidecar still says `plan_review_failed:N`, which maps to `("plan", N+1, plan_path)` → planner re-revises with the same review file.

This is consistent with the spec ("Key property: if `plan` is interrupted mid-session, `step` is either absent or from the previous attempt → re-run plan") and the planner agent session is persistent so the duplicate work is cheap. Acceptable — just confirm this is the intended semantics.

### 4. `_write_session` loses two guards — verify intended

The current implementation has:

```python
if not plan_path.exists() or not session_id:
    return
```

The new sidecar version (per spec §1) has no such guard. Confirmed by walking the call sites: this is safe in practice because

- `agents.py` only calls `_write_session(plan_path, "planner"/"implementer", self.session_id)` after `_run_claude` has returned a non-empty session id (or the run raised), and
- `main.py` only calls `_write_session(plan_path, "elapsed", …)` and the new `step` writes after `plan_path.exists()` is already true.

If an empty string somehow leaks through (e.g. session id was never received from a malformed stream), the JSON file gets `"planner": ""`, which round-trips to `sessions.get("planner") == ""`. `_run_claude` already treats `session_id=""` as falsy (`if session_id:` at line 100) and falls back to system_prompt. So no regression.

Worth a one-line note in Task 1 explicitly saying "this is intentional — verified no caller passes empty values or a missing plan path."

### 5. Type annotation drift on `_read_sessions`

Current: `_read_sessions(plan_path: Path) -> dict[str, str]`. Spec §1 shows just `-> dict`. After the change, JSON values are technically `Any`, but in practice every value written is a `str` (session ids, `str(int(elapsed))`, the new `step` strings). Recommend keeping `-> dict[str, str]` to preserve the existing contract that consumers in `main.py` rely on (`int(sessions.get("elapsed", "0"))`, etc.). Minor — call out in Task 1.

### 6. Plan + sidecar will be committed by `_git_commit` (git add -A)

`_git_commit` in `main.py` line 50 stages everything with `git add -A`. The new `{slug}.json` sidecars will therefore be committed to the target project's repo, just like the old HTML comment block was committed inside the plan `.md`. Same exposure level (session ids end up in git history either way). Not a regression, but worth a one-line confirmation in the plan that this is intended — and that running this on a project that previously committed the HTML-comment plans will leave stale comment blocks in those committed `.md` files (they're now harmless garbage).

### 7. In-flight migration behavior (no backward compat)

The plan's "Do NOT keep any backward-compat fallback to the HTML comment" choice means: on upgrade, any currently-paused milestone (plan exists, HTML comment present, no `.json` sidecar yet) will

- read `elapsed_offset = 0` → start the wall-clock from zero,
- lose the `planner`/`implementer` session ids → start fresh sessions,
- fall through to the existing heuristic for step detection (which is the very bug we're fixing).

This is acceptable because the entire point of this milestone is to fix the heuristic going forward, and any "lost" plan can still be picked up by the heuristic exactly as it does today. Worth one explicit sentence in the plan's Context section so the user (max) knows to drain in-flight milestones before deploying this change, or accepts the restart.

### 8. Refactor mode coverage (clarification, not a bug)

`process_refactor_milestone` shares `_detect_milestone_step` with implement mode. Task 3's modification adds an early-return path keyed off `sessions.get("step")`. Because Tasks 2/4 only write `step` from `process_milestone()` and `process_test_milestone()`, refactor-mode sidecars will never contain a `step` key, so the function falls through to the heuristic block. The plan correctly states "refactor-mode plans rely on this fallback too" — confirmed correct against the code at lines 284–290. No change needed, just calling out that the reviewer verified this path.

### 9. `_write_session` for refactor mode still writes the sidecar

After this change, `process_refactor_milestone` will start writing `{slug}.json` sidecars too (only with `planner`/`implementer`/`elapsed` keys, no `step`). Different from "HTML comment in plan .md" but functionally equivalent. Confirmed safe — `_read_sessions` returns the partial dict and consumers tolerate missing keys.

## Positive Notes

- Plan correctly identifies that the canonical-seq resolution block (lines 77–91) must run **before** the new `step` read, so that resumed milestones with renumbered files still find their sidecar via the correct `plan_path`.
- Task ordering (1 → 2/3 → 4/5) and dependencies are sound; commits are split sensibly along agent vs. main, implement vs. test.
- Test-mode mapping correctly diverges (`"implemented"` → `("test_run", 1)` and `"test_run_failed:N"` → `("implement", N+1)`); it would have been easy to copy-paste the implement-mode mapping by mistake.
- Plan explicitly preserves the heuristic block as fallback rather than deleting it — this keeps refactor mode working and gives a safety net for any unexpected `step` value.
- Plan correctly identifies that `import json` is already present at line 6 of `agents.py` — no spurious "add import" task.
- Task 1's call out that `_SESSIONS_RE` lives at line 25 and the old read/write live immediately below is precise — implementer won't have to hunt.

## Recommendation

The plan is fundamentally sound and the design fixes the stated bug. Before implementation, please clarify items **1** (placement of the `plan_reviewed` write — pick option (a) or (b)) and **2** (decide whether to add a post-review `step` write or accept the redundant-review window). Items 3–9 are nice-to-have clarifications.

With item 1 resolved (it's a small but real ambiguity), this plan is ready to implement.

PLAN_REVIEW_PASS
