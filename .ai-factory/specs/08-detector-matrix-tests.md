# Tests-first — complete the resume-dispatch matrix for both step-detectors (for task 06)

**Date:** 2026-07-09
**Source:** conversation context

## Why this is its own milestone

Task 06 unifies `process_milestone`/`process_test_milestone` and their step-detectors. The processors themselves drive agents and subprocesses (loud / non-deterministic — not unit-testable), so the **only** safety net for that refactor is the step-detector: a pure function `(sidecar step + files on disk) → (step, counter, plan_path)`. It is a silent-failure surface (a wrong resume dispatch does the wrong work with no crash — `test-philosophy` says test it). `tests/test_main.py` already covers `_validate_sidecar_step` well and **some** detector branches, but the matrix is **incomplete**. This milestone completes it — as **green characterization** over current behaviour — so the dedup in task 06 has a full net. All assertions pass on today's code; task 06 must keep them green.

## Gaps to fill (both detectors, every return branch pinned)

`_detect_milestone_step` — add the currently-uncovered branches:
- sidecar `plan_reviewed` → `("implement", 1)`
- sidecar `plan_review_failed:N` → `("plan", N+1)`
- heuristic: no plan-review files → `("plan_review", 1)`
- heuristic: latest plan-review not `PLAN_REVIEW_PASS` → `("plan", len+1)`
- heuristic: passing plan-review + dirty tree + no review files → `("review", 1)`
- heuristic: latest review not `REVIEW_PASS` → `("implement", len+1)`
- heuristic: all complete (latest review `REVIEW_PASS`) → `("done", 0)` — **the implement-mode `done` path is currently untested**

`_detect_test_milestone_step` — mirror the symmetric gaps:
- sidecar `planned` → `("plan_review", 1)`; sidecar `plan_review_failed:N` → `("plan", N+1)`
- heuristic: no plan-review → `("plan_review", 1)`; latest plan-review not passing → `("plan", len+1)`
- heuristic: clean tree (after passing plan-review) → `("implement", 1)`
- heuristic: no test-run files → `("test_run", 1)`; latest test-run not `TEST_PASS` → `("implement", len+1)`

Reuse the existing `_dms_dirs`/`_dtms_dirs` fixtures and git-tree setup patterns already in `test_main.py`; do not restructure the existing tests.

## What NOT to test (loud / out of scope)

- The processor loop, agent calls, git commit, `notify` — driven by external processes; not the detector's job.
- Do not add tests for task 05's exception routing here — that is milestone 07.

## Verify

- `uv run pytest tests/test_main.py` — every detector return branch above is now asserted and **green on current code** (this is characterization, not red-first). After task 06 unifies the detectors, the same suite stays green.
