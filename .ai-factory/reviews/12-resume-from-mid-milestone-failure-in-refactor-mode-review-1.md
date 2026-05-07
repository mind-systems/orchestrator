## Code Review: Resume from mid-milestone failure in refactor mode

### Summary
`process_refactor_milestone()` now calls `_detect_milestone_step()` at the top to detect where a previous run stopped and skips already-completed steps. The implementation mirrors the existing pattern in `process_milestone()` with correct refactor-specific behavior preserved.

### Critical Issues
(none)

### Correctness
All seven resume scenarios verified:
- Fresh start, plan exists but no reviews, plan review failed, plan review passed + clean tree, implementation done but no verify, verify failed, all done — each threads the correct counter through to the right loop start point and skips the right steps.
- `step` mutation from `"plan"` to `"plan_review"` at line 299 correctly feeds into the `if step in ("plan", "plan_review"):` guard at line 302.
- `impl_start` calculation at line 333 correctly distinguishes "resuming mid-implement/verify" (`counter`) from "just finished plan review" (`1`).
- The `step == "review" and iteration == counter` skip at line 335 correctly sends resume-from-verify straight to `refactor_planner.verify()` without redundant implementation.

### Behavioral Differences from process_milestone (intentional)
- Refactor raises `PipelineStopError` on max iterations (vs implement's WARNING + continue) — preserved correctly.
- Patch bridging (`review_path` → `patches_dir`) on verify failure — preserved correctly.
- No `implement_reviews` state tracking — correct, refactor flow has no equivalent `run_refactor_review`.

REVIEW_PASS
