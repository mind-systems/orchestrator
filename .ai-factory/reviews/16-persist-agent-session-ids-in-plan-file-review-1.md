# Code Review: 16-persist-agent-session-ids-in-plan-file

## Summary

Implementation matches the plan and the design captured in `notes/03`. Helpers are placed correctly, `_write_session` is called at all three sites, restoration runs at the right point in both `process_milestone()` and `process_test_milestone()`, and refactor flow is correctly left untouched. No correctness or security issues.

## What I verified

1. **`agents.py:5–11` imports** — `import re` is alphabetically placed between `os` and `subprocess`. ✓
2. **`agents.py:25–63` helpers** — `_SESSIONS_RE`, `_read_sessions`, `_write_session` match `notes/03` verbatim. Edge cases (missing file, missing block, missing role, empty `session_id`) are guarded. ✓
3. **`agents.py:255` (in `PlannerReviewer.plan`)** — `_write_session(plan_path, "planner", self.session_id)` immediately after the `_run_claude` call that assigns `self.session_id`. ✓
4. **`agents.py:278` (in `PlannerReviewer.review`)** — same persistence after `_run_claude`. ✓
5. **`agents.py:395` (in `Implementer.implement`)** — `_write_session(plan_path, "implementer", self.session_id)` after `_run_claude`. ✓
6. **`main.py:13` import** — `_read_sessions` added to the agents import. ✓
7. **`main.py:169–172` `process_milestone()`** — restore block is after `implementer = Implementer(project_dir)` and before `if step == "plan":`. So plan revisions (counter > 1) re-use the planner session, and implement/review resumes restore both. ✓
8. **`main.py:555–558` `process_test_milestone()`** — same restore block after `test_runner = TestRunner()`, before the plan step. ✓
9. **`process_refactor_milestone()`** — no restore block added, per scope. ✓ (Note: `Implementer.implement()` still writes a sessions block when invoked from refactor, but that data is never read back — see Observation 1.)

## Runtime correctness checks

- **Type compatibility:** `sessions.get("planner")` returns `Optional[str]`, assigned to `session_id: str | None`. ✓
- **First-run safety:** when `plan_path` does not yet exist (counter == 1, step == "plan"), the `if plan_path.exists():` guard skips restoration, leaving `session_id = None`. `_run_claude` then takes the fresh-session branch with `--system-prompt`. ✓
- **Plan revision overwrite:** when `PlannerReviewer.plan(..., plan_review_path=...)` instructs Claude to rewrite the plan file, the trailing HTML block may be erased by the agent's `Write` call. `_write_session` runs immediately after and re-adds the `planner:` line. There is no `implementer:` line at that point (revision only happens in the plan/plan_review phase), so nothing is lost. ✓
- **Session ID updates on `--resume`:** `_run_claude` always re-assigns `self.session_id` from the final JSON event, even when resuming. The post-call `_write_session` keeps the stored ID current. ✓
- **No concurrency:** orchestrator processes one milestone at a time, so the non-atomic read/write of `plan_path` in `_write_session` is safe. ✓
- **Block round-trip:** writing `planner: X` first, then `implementer: Y` produces a block with both lines and order preserved on subsequent updates. Verified by reading the helper logic. ✓

## Observations (non-blocking)

1. **Refactor flow writes dead data.** `Implementer.implement()` is shared with `process_refactor_milestone()`, so the new `_write_session` call also fires there, accumulating an `implementer:` line in refactor plan files that is never read back (refactor mode does not restore). This is consistent with the scope note in `notes/03` ("RefactorPlanner already tracks its own session in-memory") and is harmless — but it means *if* a refactor run is interrupted, the implementer's mid-fix context is still lost, even though it would have been recoverable from disk. Out of scope per the plan; flagging for future awareness.

2. **Unrelated change to `_run_claude` error formatting.** `agents.py:177–181` removes the `stderr[:1000]` and `stdout[:500]` truncation when raising `RuntimeError` after a non-zero CLI exit. This isn't a task in the plan; it's an unrelated debugging improvement (matches the "full stdout is now shown" remark in `notes/03`). Behavior change: error messages can now be very large if the CLI produced lots of output, but that's the point — better diagnostics. Not a defect, just scope creep worth noting.

3. **Hardcoded role strings.** `"planner"` and `"implementer"` are string literals in 3 sites in `agents.py` and 2 in `main.py`. A typo would silently produce dead writes or empty restorations. Acceptable for two roles; consider constants if more roles are ever added.

4. **`_write_session` non-atomic write.** Read-then-write on the same path. A SIGKILL between the read and the write could truncate the plan file. Consistent with all other file writes in this codebase, and the orchestrator already handles interrupted runs by re-deriving state from disk. Not a defect; flagging because the whole point of this milestone is crash resilience.

## Security / migration

- HTML comment block is invisible to markdown renderers and ignored by all agents reading the plan as context. No information leakage beyond what `.ai-factory/plans/` already contains.
- No CLI/API surface changes. Existing plan files without the block are read as empty session dicts (correct).
- No external migrations.

REVIEW_PASS
