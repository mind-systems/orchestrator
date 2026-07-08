# Express the milestone pipeline once (implement / test)

**Date:** 2026-07-09
**Source:** conversation context

## Problem today

`main.py` holds two ~95%-identical pipelines:

- `process_milestone` (252–403, ~154 lines) — plan → implement → **review** loop.
- `process_test_milestone` (519–662, ~146 lines) — plan → implement → **test-run** loop.

And the same duplication runs one level down in their step-detectors:

- `_detect_milestone_step` (163–249) vs `_detect_test_milestone_step` (446–516). `_validate_sidecar_step` (114–160) is **already** shared and parametrized — the detectors only differ in the same vocabulary the processors differ in.

This duplication is the structural reason the run-outcome classification could be got wrong: the `PipelineStopError` raise sites, the step vocabulary, and the resume logic each live in **two** places that must be kept in lockstep by hand. Collapsing to one home makes a whole class of "edit one, miss the twin" mistakes impossible.

## The only real divergences (full set — verified by reading both)

| Concern | implement | test |
|---|---|---|
| Roadmap file | `roadmap_filename` param (`ROADMAP.md`) | `ROADMAP_TESTS.md` (hardcoded) |
| Header print | `MILESTONE:` | `TEST MILESTONE:` |
| Planner prompt | `planner_prompt_name` param (`planner`) | `test-planner` (hardcoded) |
| Output dir | `reviews/` | `test-runs/` |
| Output artifact | `{seq}-{slug}-review-{n}.md` | `{seq}-{slug}-test-{n}.txt` |
| Verify-step name | `review` / `review_failed:` | `test_run` / `test_run_failed:` |
| Detector done-signal | `REVIEW_PASS` | `TEST_PASS` |
| Extra agent | — | `TestRunner()` |
| Verify call | `planner_reviewer.review(plan_path, out, prev_review_path=…)` | `test_runner.run(plan_path, out, project_dir)` |
| Prev-output re-check | **yes** — implement threads `prev_review_path` (main.py:375–380) into the reviewer for per-finding re-verification | **no** — `TestRunner.run` is stateless |
| Pass print | `REVIEW PASSED` | `TESTS PASSED` |
| Fail print | `Review found issues` | `Tests failed` |
| Fail-raise message | `Max iterations … without REVIEW_PASS` | `Tests failed after N iteration(s)` |

**Everything else is identical** and becomes shared body: dir setup, `seq`/`plan_path` scheme, `_read_sessions`/elapsed offset, resume print, the `done` branch (mark_done + `_git_commit` + `milestone` notify), agent construction + session wiring, the plan step, the **entire** plan-review loop and its no-passing-plan-review safety guard, the `impl_start > max_iterations` resume-past-max guard, the mid-loop resume skip, and the mark-done/commit/notify tail.

## The refactor

- Introduce one small `mode` descriptor (a frozen dataclass or `NamedTuple`) carrying the static fields above: `roadmap_filename`, `header_label`, `planner_prompt_name`, `output_dirname`, `output_suffix` (e.g. `-review-{n}.md`), `verify_step` (`review`/`test_run`), `verify_fail_tag`, `pass_signal` (`REVIEW_PASS`/`TEST_PASS`), and the pass/fail/raise label strings.
- The two behavioural differences that need runtime state (the verify call and its prev-output threading) are supplied as a **closure built after the agents are constructed**: `verify(iteration, out_path, prev_out_path) -> bool`. Implement's closure calls `planner_reviewer.review(plan_path, out_path, prev_review_path=prev_out_path)`; test's calls `test_runner.run(plan_path, out_path, project_dir)` and ignores `prev_out_path`. Test mode builds `prev_out_path` as `None` (or the shared body simply passes it and the closure drops it) — the prev-output re-check must remain implement-only.
- Collapse `_detect_milestone_step` + `_detect_test_milestone_step` into one detector parametrized by `(verify_step, verify_fail_tag, output_dirname, output_suffix, pass_signal)`; `_validate_sidecar_step` stays as-is (already shared).
- `process_milestone(project_dir, milestone, index, config, mode, phase_session_id)` becomes the single entry. `_implement_loop` / `_test_loop` each construct their `mode` and call it. Keep the existing `planner_prompt_name` / `roadmap_filename` parameters reachable so the implement variant that passes non-defaults still works.

## Invariants to preserve (this is a pure refactor — zero behaviour change)

- Resume from **every** `step` value dispatches exactly as today, in **both** modes: `plan`, `planned`→`plan_review`, `plan_review_failed:N`, `plan_reviewed`→`implement`, `implemented`→verify, verify-step mid-loop skip (`review`/`test_run` at `iteration == counter`), `review_failed:N`/`test_run_failed:N`, `done`.
- The stale-sidecar fallthrough to the heuristic (via `_validate_sidecar_step`) is unchanged.
- Implement keeps `prev_review_path` re-verification; test never grows one.
- The `HaltError` / `PipelineStopError` split from task 05 is preserved: after unification each collapsed raise site keeps whichever exception 05 assigned it (plan-fail / no-passing-plan-review / verify-fail / signature → `PipelineStopError`; resume-past-max → `HaltError`). Usage-limit and the manual/cli halts live outside these functions and are untouched.
- Artifact names, sidecar `step` strings, print lines, and commit/notify behaviour are byte-for-byte the same.

## Tests — the safety net for this refactor

The step-detector is the only unit-testable core (the processor loop drives agents/subprocess). A tests-first milestone (`.ai-factory/specs/08-detector-matrix-tests.md`) completes the resume-dispatch matrix for both detectors **before** this task, all green on current code. This refactor must keep that suite green:
- Preserve the detectors' tested public behaviour. If unification collapses `_detect_milestone_step` / `_detect_test_milestone_step` into one parametrized function, either keep the two names as thin wrappers or update the tests' calls **in the same commit** — renaming an entry point is acceptable Class-A drift, a changed dispatch result is a Class-B silent bug and is not.
- After the change, `uv run pytest` stays green with no assertion weakened.

## Verify

- Diff a dry run of both modes against the current behaviour on the same roadmap: identical console output, identical artifact filenames, identical sidecar `step` progression.
- Resume matrix: for each `step` above, hand-seed a sidecar and confirm the resumed run picks the same next action in implement and in test mode.
- Confirm implement still passes the previous review file to the reviewer on iteration ≥2, and test still does not.

## What NOT to do

- Do not change any observable behaviour — this is dedup only. If a "simplification" would alter output, artifact names, or resume dispatch, don't.
- Out of scope (separate tasks): splitting signal handling / usage checks / git into their own modules. This task unifies the milestone pipeline only.
- Do not touch `agents.py`, `notify.py`, the prompts, or the on-disk artifact protocol.
- Do not reorder task 05: this depends on 05 having landed. Touch `main.py` only.
