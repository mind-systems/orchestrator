# Resume markers carry their iteration index — `planned:N` and `implemented:N`

**Date:** 2026-07-22
**Source:** conversation context (the `implemented` half observed on resume after the spec-31 crash; the `planned` half found by inspecting the plan-loop's resume symmetry)

## Problem today

Each phase has an iterative loop, and each loop writes a step marker to the JSON sidecar. The **fail** markers carry their ordinal — `plan_review_failed:N` (`main.py:301`) and `review_failed:N` / `test_run_failed:N` (`main.py:348`), both parsed back on resume (`resume.py:124-126,131-133`). But the two **"artifact produced"** markers — `planned` and `implemented` — are written bare, without the iteration they belong to. That drops state on resume, differently in each loop.

**Implement loop — the index is lost.** The implement→verify loop writes `_write_session(plan_path, "step", "implemented")` **before every verify pass** (`main.py:329`), identically for iteration 1, 2, 3… When a run dies **inside** the verify call (`_verify`, `main.py:340`) the last marker is a bare `implemented`, which `_detect_step` maps with a **hardcoded counter of 1** (`resume.py:129-130`). The verify iterations already run — their `…-review-N.md` artifacts on disk — are consulted nowhere. Consequences, all from the reset counter:

1. **Iteration budget resets.** The verify loop restarts at `range(1, max_iterations + 1)` (`main.py:321`), granting a fresh full budget on top of the rounds already spent — a task can exceed `max_iterations` across a resume. (The `impl_start > max_iterations` guard at `main.py:316-320` never fires because `impl_start` is 1.)
2. **The prior verify artifact is overwritten.** At iteration 1, `out_path = …-review-1.md` (`main.py:334`) and `review()` writes there — clobbering the real review-1 (uncommitted until the task completes, so the overwrite is permanent loss).
3. **Re-review semantics are lost.** `prev_out_path` is set only when `iteration > 1` (`main.py:336-339`); at iteration 1 it is `None`, so `review(..., prev_review_path=None)` runs a **fresh** review instead of the "verify each prior finding was fixed" re-review.

Real case (right after the spec-31 crash): a task at review iteration 3 resumed as `Resuming from step 'review' (counter=1)` → `REVIEWING (iteration 1)`.

**Plan loop — no "revised plan ready" marker at all.** The plan-review loop writes `planned` once (`main.py:277`), then per failed attempt writes `plan_review_failed:N` (`main.py:301`) and immediately re-plans (`main.py:302-305`) — with **no marker** recording that the revised plan for attempt N+1 is now on disk. So a crash **during plan-review attempt N+1** leaves the stale `plan_review_failed:N` as the last marker, which `_detect_step` maps to `("plan", N+1)` (`resume.py:124-126`) → the plan block (`main.py:263`) **re-runs the planner** before re-reviewing. The planner already produced that exact plan pre-crash; the resume regenerates it — a wasted planner call (an expensive LLM invocation) on every resume that lands mid-plan-review beyond attempt 1.

This is not the same failure as the implement side — the attempt index is preserved (in `plan_review_failed:N`), so nothing is overwritten and the budget is not reset. But it is the **exact asymmetry** with the implement loop, which never re-runs the implementer on resume (its `implemented` marker sits right before verify). One loop is resume-precise; the other burns a redundant plan run. Both stem from the same root: the "artifact produced" marker has no index.

## The fix

Give **both** "artifact produced" markers their iteration index, symmetric with the fail markers. Clean break — no bare `planned` / `implemented` fallback (owner decision: no legacy branch). After the fix the two loops carry identical marker shapes:

```
plan:      planned:1 → plan_review_failed:1 → planned:2 → … → plan_reviewed
implement: implemented:1 → review_failed:1 → implemented:2 → … → (pass → done)
```

**Implement side** (backend-neutral — `main.py:329` serves both `review` and `test_run`, so test mode is covered):

1. Write the ordinal: `main.py:329` → `f"implemented:{iteration}"`.
2. `_detect_step`: `implemented:N` → `(verify_step, N, plan_path)` (replaces the `== "implemented"` branch, `resume.py:129-130`).

**Plan side** (the new half):

3. Index the plan-ready marker: `main.py:277` → `f"planned:1"`; and **after the re-plan** (end of the loop body, following `main.py:305`) add `_write_session(plan_path, "step", f"planned:{attempt + 1}")` — records "the revised plan for attempt N+1 is written; review it, do not re-plan."
4. `_detect_step`: `planned:N` → `("plan_review", N, plan_path)` (replaces the `== "planned"` branch, `resume.py:122-123`). `plan_review_failed:N` → `("plan", N+1)` stays unchanged — it is the correct resume for a crash **during the re-plan itself** (the window between writing `plan_review_failed:N` at 301 and `planned:(N+1)` at the body's end).

**Both, in `_validate_sidecar_step`** (`resume.py:11-57`): add explicit `planned:N` and `implemented:N` branches — always valid, no artifact reference (the plan `.md` / working tree proves existence; there is no per-attempt numbered file to stat). Parse-guard a malformed `:N` exactly as the `fail_prefix` branch does (`resume.py:48-55`): a non-integer tail clears the value so dispatch falls through to the heuristic. **Drop both `planned` and `implemented` from the bare always-valid tuple** (`resume.py:31`) — that tuple becomes empty, so the `if step_value in (...)` check is removed; every marker is now either indexed or artifact-gated.

No guard is needed in the plan loop analogous to the implement loop's `iteration == counter` short-circuit (`main.py:322-324`): the plan loop reviews at the **top** of the body and re-plans at the **bottom**, so resuming into `("plan_review", N)` reviews attempt N immediately without re-planning. The implement loop needs its guard only because it implements at the top.

**Migrate the one wounded sidecar.** The clean break means the single sidecar written under the old bare marker must be migrated with this change or it falls through to the heuristic. The only affected file is `repo-stats-herald`'s `.ai-factory/plans/34-6-2-coordination-root-seeding.json` — it holds `"step": "implemented"` after a crash during review iteration 3 (reviews 1 and 2 on disk, neither `REVIEW_PASS`). Set its `step` to `"implemented:3"` so post-fix resume lands on review iteration 3, reads `review-2.md` as prior, writes `review-3.md`. One-time data migration in the target project, not orchestrator code; it only makes sense once this task's code is in effect (resume `repo-stats-herald` only after `resume.py`/`main.py` carry the fix). No sidecar carries a bare `planned` — no plan-side migration needed.

With that, the spec-31 incident resumes as `(verify_step, 3)`: `impl_start = 3`, the guard `iteration == counter` short-circuits implement, a fresh `review-3.md` is written (no overwrite), `review-2.md` is read as prior. And a crash mid-plan-review at attempt N resumes as `("plan_review", N)` — review only, no redundant planner run.

## Tests

The grammar contract and its tests are task **18.2.1** (spec `34-marker-index-grammar-red-tests.md`) — they already sit in `tests/test_main.py`, authored against the post-fix `:N` grammar and red/heuristic-coincident against today's code. This task (18.2.2) implements the marker indexing in `main.py` + `resume.py` so those assertions go **green** and are driven by the explicit branches (not the disk heuristic); it adds no new tests. If any assertion in 18.2.1 still passes only via the heuristic after this task, that is a defect in this task — the dispatch must be explicit.

## Verify

- `uv run pytest` green, including the flipped `:N` cases.
- Reasoning trace, implement side: `step = "implemented:3"` → resumes review iter 3, writes `review-3.md`, reads `review-2.md`, no re-implement.
- Reasoning trace, plan side: a crash during plan-review attempt 2 leaves `step = "planned:2"` → resumes `("plan_review", 2)` → reviews attempt 2 with **no** planner run; a crash during the re-plan leaves `step = "plan_review_failed:1"` → resumes `("plan", 2)` → re-plans (correct).

## What NOT to do

- Do **not** keep a bare-`planned` or bare-`implemented` fallback "just in case" — the removal is deliberate (clean code, no legacy branch); the one wounded sidecar is migrated by hand, so no bare marker survives.
- Do **not** give `planned:N` / `implemented:N` an artifact-existence check — unlike `plan_review_failed:N` / `review_failed:N` (gated on the review file), these have no numbered artifact; validity is structural.
- Do **not** change the `plan_review_failed:N` → `("plan", N+1)` or `review_failed:N` → `("implement", N+1)` dispatch, or `plan_reviewed` — only the two "artifact produced" markers gain an ordinal.
- Do **not** add a resume short-circuit guard to the plan loop — it reviews-first, so none is needed; and do **not** alter the implement loop's guard (`main.py:322-324`) or the `max_iterations` guard (`main.py:316-320`).
- Orchestrator code changes are confined to `main.py` and `resume.py` — the grammar tests already landed in 18.2.1 (`tests/test_main.py`); do not re-add or weaken them here, just make them green via the explicit dispatch. The only file touched outside this repo is the one-time sidecar migration in `repo-stats-herald` (`.ai-factory/plans/34-6-2-coordination-root-seeding.json`).
