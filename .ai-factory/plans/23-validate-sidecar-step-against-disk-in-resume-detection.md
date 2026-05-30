# Plan: Validate sidecar `step` against disk in resume detection

## Context
After `milestone-rescue` cleans up artifacts, the sidecar's `step` value can reference files that no longer exist (e.g. `plan_review_failed:2` while `plan-review-2.md` has been deleted), causing the planner to receive a non-existent path. This milestone hardens `_detect_milestone_step()` and `_detect_test_milestone_step()` in `orchestrator/main.py` so a stale/incorrect `step_value` is detected and ignored, letting the heuristic block re-derive the correct resume point.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Implement validation

- [x] **Task 1: Add sidecar-step validation in `_detect_milestone_step()`**
  Files: `orchestrator/main.py`
  In `_detect_milestone_step()` (currently around lines 97–113), after reading `step_value = sessions.get("step", "")` and before the dispatch `if step_value:` block, insert a validation step that checks whether the artifact referenced by `step_value` actually exists on disk. If the referenced artifact is missing, set `step_value = ""` so execution falls through to the heuristic block (steps 3–8) instead of trusting the stale sidecar value. Validation rules:
  - `"planned"` → always valid (no artifact reference).
  - `"plan_review_failed:N"` → requires `plan_reviews_dir / f"{seq}-{slug}-plan-review-{N}.md"` to exist; if missing, clear `step_value`.
  - `"plan_reviewed"` → requires at least one file in `plan_reviews_dir.glob(f"{seq}-{slug}-plan-review-*.md")` whose contents end with `PLAN_REVIEW_PASS` (use `.read_text().strip().endswith("PLAN_REVIEW_PASS")`); if none, clear `step_value`.
  - `"implemented"` → always valid (no artifact reference; git tree state is what the heuristic later checks).
  - `"review_failed:N"` → requires `reviews_dir / f"{seq}-{slug}-review-{N}.md"` to exist; if missing, clear `step_value`.
  Keep the existing `# unrecognized → fall through to heuristic` semantics: any unrecognized `step_value` continues to fall through. Use the already-canonicalised `seq` (resolved from `plans_dir.glob(f"*-{slug}.md")` earlier in the function) when constructing artifact paths. Parse `N` defensively — wrap the `int(step_value.split(":")[1])` parse so a malformed value also clears `step_value` rather than raising.

- [x] **Task 2: Add sidecar-step validation in `_detect_test_milestone_step()`** (depends on Task 1)
  Files: `orchestrator/main.py`
  Apply the same pattern in `_detect_test_milestone_step()` (currently around lines 340–356). Validation rules:
  - `"planned"` → always valid.
  - `"plan_review_failed:N"` → requires `plan_reviews_dir / f"{seq}-{slug}-plan-review-{N}.md"` to exist.
  - `"plan_reviewed"` → requires at least one `plan_reviews_dir.glob(f"{seq}-{slug}-plan-review-*.md")` ending with `PLAN_REVIEW_PASS`.
  - `"implemented"` → always valid.
  - `"test_run_failed:N"` → requires `test_runs_dir / f"{seq}-{slug}-test-{N}.txt"` to exist; if missing, clear `step_value`.
  Same defensive `int(...)` parse for the `:N` forms. Use the canonicalised `seq` resolved at the top of the function.

- [x] **Task 3: Factor shared validation into a small helper (optional refactor)** (depends on Tasks 1 and 2)
  Files: `orchestrator/main.py`
  If the two validation blocks duplicate substantial logic, extract a private helper (e.g. `_validate_sidecar_step(step_value, seq, slug, plan_reviews_dir, artifact_dir, fail_prefix, fail_suffix) -> str` returning the original `step_value` when valid or `""` when invalid). Keep the helper internal (underscore-prefixed) and call it from both detect functions. Skip this task if the duplication is minimal (≤4 lines per site) — clarity over abstraction.
