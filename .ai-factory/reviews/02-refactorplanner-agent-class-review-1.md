# Review: RefactorPlanner agent class

## Summary

The `RefactorPlanner` class is added to `agents.py` following the exact same patterns as the existing `PlannerReviewer` class. Two methods: `audit_and_plan` (first call, sets session) and `verify` (subsequent calls via `--resume`, file-based pass/fail).

## Findings

### 1. Constructor — correct
- Loads prompt via `_load_prompt("refactor-planner")` — file exists at `orchestrator/prompts/refactor-planner.md`. No runtime error.
- Default `model="opus"`, `effort="high"` — matches the pattern and CLAUDE.md guidance for planner-class agents.
- Tools list `["Read", "Write", "Glob", "Grep", "Bash"]` — same as `PlannerReviewer`. Write is needed because the agent writes the plan file. Correct.
- `session_id` initialized to `None`. Correct.

### 2. `audit_and_plan` — correct
- Always passes `system_prompt` (first call sets the session). This matches `PlannerReviewer.plan` which also always passes `system_prompt` on the planning call.
- Stores `session_id` from the response. Subsequent `verify` calls will resume this session.
- Prompt includes milestone title, description, and output path — sufficient for the refactor-planner system prompt's "Iteration 1: Audit → Plan" instructions.

### 3. `verify` — correct
- Uses the `system_prompt if not self.session_id else None` guard — same pattern as `PlannerReviewer.review`. When `session_id` exists (normal flow after `audit_and_plan`), it resumes via `--resume` without re-sending the system prompt.
- File-based `REVIEW_PASS` detection: reads `review_path`, checks `strip().endswith("REVIEW_PASS")`. Identical to `PlannerReviewer.review`. Correct.
- Returns `False` if the review file doesn't exist (agent failed to write it). Safe fallback.

### 4. Session continuity
- `audit_and_plan` sets `self.session_id`. `verify` passes it to `_run_claude` with `--resume`. The `_run_claude` function (line 58-61) correctly uses `--resume` when `session_id` is truthy, and falls back to `--system-prompt` otherwise. No issue.

### 5. Edge case: `verify` called before `audit_and_plan`
- If `verify` is called first, `session_id` is `None`, so it sends the system prompt and creates a new session. This is a degenerate case but won't crash — same behavior as `PlannerReviewer.review` when called without a prior `plan`. Not a bug since the orchestrator (`process_refactor_milestone` in the next milestone) will always call `audit_and_plan` first.

### 6. Not yet imported in `main.py`
- Correct — the next milestone ("process_refactor_milestone function") will add the import. No dangling reference.

## Verdict

No bugs, no security issues, no correctness problems. The class faithfully follows established patterns and the prompt file exists.

REVIEW_PASS
