# Code Review: Phase-persistent PlannerReviewer session

**Plan:** `.ai-factory/plans/24-phase-persistent-plannerreviewer-session.md`
**Files reviewed (in full):** `orchestrator/roadmap.py`, `orchestrator/main.py`, `orchestrator/agents.py` (relevant methods), `docs/target-project.md`

## Scope of changes

- `roadmap.py` — `Milestone.section: str | None = None` field + `current_section` tracking in `parse_roadmap()`.
- `main.py` — `process_milestone()` / `process_test_milestone()` accept `phase_session_id` and return `str | None`; session priority logic; inlined loops in `_implement_loop()` / `_test_loop()` with section-boundary reset.
- `docs/target-project.md` — Russian "Фазы" section describing the behavior.

## Correctness verification

- **Dataclass change (roadmap.py:18).** `section` added last with a default, so the only constructor site (`roadmap.py:67`) and the `slug` property are unaffected. No positional-arg breakage. ✅
- **Section tracking (roadmap.py:47-67).** Heading detection runs at the top of the loop, ahead of the `marker_found` early-`continue`, so `current_section` updates on every line as the spec required. `lstrip("#").strip()` yields `Phase 1: X` for `## Phase 1: X` and `Sub` for `### Sub`. Headings never match `CHECKBOX_RE` or `---STOP---`, so collection logic is untouched; `---STOP---`, blanks, and continuation lines do not reset the section. H4+ (`#### …`) lines do not match `## `/`### ` and are correctly ignored. ✅
- **Session priority (main.py:243-249, 486-490).** `sidecar planner` → `phase_session_id` → `None` matches the spec. On a fresh second-in-phase milestone the sidecar file doesn't exist (`sessions == {}` → falsy), so `phase_session_id` is used; on a mid-milestone resume the sidecar `planner` wins, correctly reattaching that milestone's own session. The implementer assignment `sessions.get("implementer") if sessions else None` is behavior-equivalent to the original (was only set inside `if sessions:`, defaulting to the constructor's `None`). ✅
- **Return paths — every exit returns a session id.**
  - `step == "done"` (planner not yet created): returns incoming `phase_session_id` — chain continues across an already-done milestone. ✅
  - `mark_skipped` skip path: `plan()` runs `_run_claude` and assigns `self.session_id` *before* the `plan_path.exists()` check (agents.py:247-256), so `planner_reviewer.session_id` is non-`None` here. ✅
  - normal end: returns `planner_reviewer.session_id`, which `review()` keeps current (re-stored after each call). The implement→review loop always runs `review()` at least once (the `impl_start > max_iterations` guard rejects empty ranges), so the id is never left unset on the success path. ✅
  - `PipelineStopError` paths raise rather than return; the exception propagates past the loop to `cli()`, halting the run — phase threading is moot at that point. ✅
- **Loop section reset (main.py:617-624, 654-661).** `current_section`/`phase_session_id` init to `None`; `state.stop_requested` is checked first with the exact original halt string `>>> Stop requested — halting.`; `phase_session_id` is reset to `None` *before* the first milestone of each new section, guaranteeing a cold start at every `##`/`###` boundary; the return value is threaded forward. Resetting before the call (not after) is the correct ordering. ✅
- **Forked-session safety.** When `phase_session_id` is applied, `_run_claude` is invoked with a non-`None` `session_id` (→ `--resume`, system prompt omitted) — the intended warm-start. Any new/forked id minted by resume is captured into `self.session_id` and threaded onward, so the chain survives id rotation. ✅
- **Callers.** `process_milestone` is called only at main.py:661 and `process_test_milestone` only at main.py:624 — both inside the inlined loops, both assign the return value. No other callers exist, so the signature/return-type change is fully covered. `_run_loop` remains defined but unused, as the plan specified. ✅
- **Docs.** `docs/target-project.md` is in Russian, matching surrounding docs; the described behavior (one planner session per phase, reset at `##`/`###` boundaries, optional phases, headingless roadmap → single continuous session) accurately reflects the code, including the `None != None` no-reset case for flat roadmaps. ✅

## Non-blocking observations

These are consistent with the stated design (spec note `notes/10-phase-session-persistence.md`) and require no change:

1. **Flat / single-heading roadmaps reuse one session for the entire run.** With no headings (or one `## Milestones`), every milestone shares the same `section`, so the planner session is carried across all of them and context grows monotonically. The spec explicitly accepts this (Opus 1M context). A future optional safety valve could treat `section is None` as "always reset," but that is out of scope here.
2. **`done` early return drops warmth on restart.** After a process restart, a milestone re-detected as `done` returns the incoming `phase_session_id` (which is `None` post-restart, since the phase session is in-memory only) rather than its own sidecar `planner` id. This is a missed optimization, not a correctness issue, and matches the "in-memory only" design.

## Conclusion

The implementation matches the plan task-for-task, all return paths are covered, the parser change is safe and backward-compatible, the loops correctly isolate sessions at phase boundaries, and no callers break. No correctness, security, or runtime-breakage findings.

REVIEW_PASS
