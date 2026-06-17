# Plan Review: Phase-persistent PlannerReviewer session

**Plan:** `.ai-factory/plans/24-phase-persistent-plannerreviewer-session.md`
**Files targeted:** `orchestrator/roadmap.py`, `orchestrator/main.py`
**Risk Level:** 🟢 Low

## Summary

The plan carries the `PlannerReviewer` session across consecutive milestones within
the same `##`/`###` roadmap section so the planner is warm-started instead of re-reading
DESCRIPTION/ARCHITECTURE/spec notes per milestone. I verified it against the live code in
`roadmap.py`, `main.py`, `agents.py`, the spec note (`notes/10-phase-session-persistence.md`),
and `ARCHITECTURE.md`. The plan is internally consistent, matches the actual code, and
**improves on its own source docs in two places**:

- The ROADMAP.md milestone text says `process_milestone()`/`process_test_milestone()` live
  in `agents.py`. They are actually in `main.py`. The plan correctly targets `main.py`.
- The spec note's loop snippet references `_state.stop_requested`; the real module is imported
  as `state` (`from . import state`). Task 5/6 correctly use `state.stop_requested`.

## Correctness Verification

- **Session priority (Task 3/4):** sidecar `planner` → `phase_session_id` → `None` matches
  the spec and is safe. On a fresh, never-run milestone the sidecar is empty, so
  `phase_session_id` is used; on a mid-milestone resume the sidecar wins, correctly
  reattaching that milestone's own session. ✅
- **Resume semantics:** when `phase_session_id` is applied, `PlannerReviewer.plan()` passes a
  non-`None` `session_id`, so `_run_claude` uses `--resume` and omits the system prompt — the
  intended warm-start path. The returned (possibly forked) sid is re-stored, so the chain
  survives even if `--resume` mints a new id. ✅
- **Return paths (Task 3/4):** I checked every exit of `process_milestone`. `done` early
  return → passed-in `phase_session_id`; `mark_skipped` early return → `planner_reviewer.session_id`
  (set, since `plan()` ran); normal end → `planner_reviewer.session_id`. The implement→review
  loop always runs `review()` at least once (the `impl_start > max_iterations` guard prevents an
  empty range), so `session_id` is never left `None` on the normal path. `PipelineStopError`
  paths raise rather than return, which correctly halts the pipeline. ✅
- **Section reset ordering (Task 5/6):** resetting `phase_session_id = None` *before* calling
  `process_milestone` means a section's first milestone always starts cold — correct isolation. ✅
- **Heading parse placement (Task 2):** placing the `##`/`### ` check ahead of the
  `if marker_found:` early-`continue` is harmless and avoids any ordering bug; headings never
  match `CHECKBOX_RE` or the `---STOP---` line, so existing collection logic is untouched.
  `lstrip("#").strip()` yields the right text for `## Phase 1: X` and `### Sub`. ✅
- **Dataclass change (Task 1):** `section` added last with a default; the only `Milestone(...)`
  constructor site is `roadmap.py:61`, and the `slug` property is unaffected. ✅
- **Call sites:** `process_milestone` is called only at `main.py:642` and `process_test_milestone`
  only at `main.py:611`; both are inside the loops being inlined. No other callers exist, so the
  signature/return-type change is fully covered. ✅

## Context Gates

- **ARCHITECTURE.md — WARN (non-blocking).** Dependency direction `main → agents → roadmap`
  and "one class per agent" are unaffected; no new imports are introduced. Key Principle #1
  ("agents communicate through files only — no in-memory data passing between agents") is bent
  slightly: `phase_session_id` is threaded in-memory across milestone iterations. This is
  orchestration state for a single agent *role* (not planner↔implementer hand-off), the value
  is still mirrored to the sidecar by `plan()`/`review()`, and the spec note explicitly accepts
  it. No change required — flagging for alignment awareness only.
- **RULES.md — WARN.** Not present; no explicit-rule gate to apply.
- **ROADMAP.md — OK.** The work is anchored to the milestone at line 59 (`## Milestones`).
  No skill-context (`.ai-factory/skill-context/aif-review/SKILL.md`) is present, so no
  project-specific overrides apply.

## Non-Blocking Considerations

These do not require plan changes; noted for the implementer/author.

1. **Single-section / no-heading roadmaps reuse one session for the whole run.** This project's
   active roadmap sits entirely under one `## Milestones` heading, and milestones with no
   preceding heading share `section = None`. In both cases the session is carried across *every*
   milestone in the run (plan + reviews + revisions each), so context grows monotonically. The
   spec note deems this acceptable ("Opus 1M context — bloat not a concern"), and it is the
   stated design. If you want a safety valve, treating `section is None` as "always reset"
   (never reuse) would bound growth for flat roadmaps without affecting headed ones — optional.

2. **`done` early return discards the resumed milestone's own warmth.** On a restart where a
   pending-in-roadmap milestone is detected as fully `done`, the function returns the incoming
   `phase_session_id` (which is `None` after a process restart, since the phase session is
   in-memory only). Returning that milestone's *sidecar* `planner` id instead would warm the
   next milestone. This is a missed optimization, not a bug, and is consistent with the
   "in-memory only" design — leave as planned unless you want the extra warmth.

3. **Keep the halt message string identical.** Task 5/6 say to match `_run_loop`'s behavior; use
   the exact existing string `>>> Stop requested — halting.` so log output is unchanged.

## Positive Notes

- All return paths are explicitly enumerated in the plan — the easiest place to introduce a
  chain-breaking `None` was caught and handled.
- The plan corrected two inaccuracies in its own source docs (file location and `state` vs
  `_state`), showing it was checked against the real code rather than copied from the note.
- Implementer session handling is explicitly left unchanged, avoiding scope creep.
- Commit split (parse change vs. threading) is clean and reviewable.

PLAN_REVIEW_PASS
