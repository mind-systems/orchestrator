# Plan: Express the milestone pipeline once (implement / test)

## Context
Collapse the ~95%-duplicate `process_milestone`/`process_test_milestone` and their step-detectors into one parametrized function each, driven by a small `mode` descriptor plus a runtime `verify` closure — a pure, behaviour-preserving dedup so the raise sites, step vocabulary, and resume logic live in one home instead of two kept in lockstep by hand.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Mode descriptor

- [x] **Task 1: Introduce the `Mode` descriptor and build the two instances**
  Files: `orchestrator/main.py`
  Add a frozen `Mode` **`NamedTuple`** near the top of `main.py` carrying only the static per-mode divergences verified from both current functions. (Use `NamedTuple`, not `@dataclass(frozen=True)`, so `_replace` is available for the `_implement_loop` override in Task 4.)
  - `roadmap_filename` (`"ROADMAP.md"` / `"ROADMAP_TESTS.md"`)
  - `header_label` (`"MILESTONE"` / `"TEST MILESTONE"`) — the text after `>>> ` prefix in the `{'='*60}` banner
  - `planner_prompt_name` (`"planner"` / `"test-planner"`)
  - `output_dirname` (`"reviews"` / `"test-runs"`)
  - `output_suffix` — the artifact tail with an `{n}` placeholder: `"-review-{n}.md"` / `"-test-{n}.txt"`
  - `verify_step` (`"review"` / `"test_run"`) and `verify_fail_tag` (`"review_failed:"` / `"test_run_failed:"`)
  - `pass_signal` (`"REVIEW_PASS"` / `"TEST_PASS"`)
  - print/raise label strings: the skip-message (`"Planner did not create a plan (milestone may already be done). Skipping."` / `"Planner did not create a plan. Skipping."`), verify-running header (`"REVIEWING"` / `"RUNNING TESTS"`), pass line (`"REVIEW PASSED"` / `"TESTS PASSED"`), fail line (`"Review found issues"` / `"Tests failed"`), and the max-iterations raise message (`"Max iterations ({n}) reached without REVIEW_PASS."` / `"Tests failed after {n} iteration(s)."`)
  Define two module-level constants `IMPLEMENT_MODE` and `TEST_MODE` populated from the exact current literals. Do NOT wire anything to them yet — this task only introduces the descriptor so the diff stays reviewable. Every string must be copied byte-for-byte from the current code. Anchors: header `main.py:269/535`, skip-message `314/580`, verify-running header (`>>> REVIEWING` / `>>> RUNNING TESTS`) `374/638`, pass line `386/645`, fail line `389/648`, max-iterations raise `392-395/651-654`.

### Phase 2: Unify the detector

- [x] **Task 2: Collapse the two step-detectors into one parametrized detector** (depends on Task 1)
  Files: `orchestrator/main.py`
  Merge `_detect_milestone_step` (`main.py:165-251`) and `_detect_test_milestone_step` (`main.py:448-518`) into one private `_detect_step(project_dir, seq, slug, plan_path, plan_reviews_dir, output_dir, verify_step, verify_fail_tag, output_suffix, pass_signal)` that reproduces the current logic exactly:
  - The canonical seq/plan_path resolution block (identical in both) stays verbatim.
  - `_validate_sidecar_step` (already shared, `main.py:116-162`) is called with `verify_fail_tag` and `output_suffix`.
  - Sidecar dispatch: `planned`→`plan_review`, `plan_review_failed:N`→`plan`(N+1), `plan_reviewed`→`implement`, `implemented`→`verify_step`, `<verify_fail_tag>N`→`implement`(N+1).
  - Heuristic tail: no plan-review files→`plan_review`; latest plan-review not `PLAN_REVIEW_PASS`→`plan`; clean tree→`implement`; then no verify-output files→`verify_step`; latest output endswith `pass_signal`→`done` else `implement`(len+1). Confirm the implement and test tails are the same logic phrased inversely and that the unified form returns identical `(step, counter, plan_path)` for both.
  Keep `_detect_milestone_step(...)` and `_detect_test_milestone_step(...)` as thin wrappers with their **current exact signatures** (`tests/test_main.py` imports and calls both by name, positionally) that forward to `_detect_step` with the mode's `verify_step`/`verify_fail_tag`/`output_suffix`/`pass_signal` and the right output dir (`reviews` / `test-runs`). Renaming an entry point would break the tests — the wrappers must preserve the tested public behaviour so `uv run pytest` stays green with no assertion changed.

### Phase 3: Unify the processor

- [x] **Task 3: Collapse the two processors into one `process_milestone(..., mode, verify)`** (depends on Task 2)
  Files: `orchestrator/main.py`
  Merge `process_milestone` (`main.py:254-405`) and `process_test_milestone` (`main.py:521-664`) into a single function `process_milestone(project_dir, milestone, milestone_index, config, mode=IMPLEMENT_MODE, phase_session_id=None)`.
  **`mode` MUST default to `IMPLEMENT_MODE`** — a required positional 5th arg would break `test_process_milestone_resume_past_max_iterations_raises_halt_error` (`tests/test_main.py:789`), which calls `process_milestone(tmp_path, _MilestoneStub(), 1, config)` with four positional args and asserts a `HaltError` is raised. With the default, that call keeps resolving to implement mode exactly as today (planner prompt `planner`, roadmap `ROADMAP.md`) and the `impl_start(4) > max_iterations(3)` → `HaltError` path is unchanged; without it the call raises `TypeError` and the `isinstance(..., HaltError)` assertion goes red. This preserves the "pytest stays green, zero assertion changes" invariant with the test untouched.
  Shared body (identical today) is written once: dir setup (`plans/`, `mode.output_dirname`, `plan-reviews/`), `roadmap_path` from `mode.roadmap_filename`, `seq`/`plan_path` scheme, the banner using `mode.header_label`, calling the unified detector via the mode fields, `_read_sessions`/elapsed offset, resume print, the `done` branch (mark_done + `_git_commit` + `milestone` notify), agent construction (`PlannerReviewer(project_dir, planner_prompt_name=mode.planner_prompt_name)`, `Implementer`), session wiring, the plan step (using `mode` skip-message), the entire plan-review loop and its no-passing-plan-review safety guard, the `impl_start > max_iterations` `HaltError` resume-past-max guard, the mid-loop resume skip keyed on `mode.verify_step`, and the mark-done/commit/notify tail.
  The two runtime divergences are supplied as a `verify(iteration, out_path, prev_out_path) -> bool` closure built **after** the agents are constructed, plus per-mode output paths:
  - Verify-output path = `output_dir / f"{seq}-{slug}{mode.output_suffix.format(n=iteration)}"`.
  - Implement's closure calls `planner_reviewer.review(plan_path, out_path, prev_review_path=prev_out_path)`; test's calls `test_runner.run(plan_path, out_path, project_dir)` and ignores `prev_out_path`.
  - `prev_out_path` is computed **only** for implement (the `iteration > 1` + `prev.exists()` guard from `main.py:377-381`); in test mode it is `None` — the prev-output re-verification must stay implement-only. Construct `TestRunner()` only in test mode.
  - Sidecar `step` writes use `mode.verify_step` / `mode.verify_fail_tag` so the strings written to disk are byte-for-byte unchanged (`implemented`, `review`/`test_run`, `review_failed:N`/`test_run_failed:N`).
  - The verify-loop prints (`mode.verify_running_header`, pass/fail lines) and the max-iterations raise use `mode` labels; keep the `subprocess.run(["git","add","-A"], check=True)` before each verify call.
  Preserve the task-05 exception split at every collapsed raise site: plan-fail / no-passing-plan-review / verify-fail → `PipelineStopError`; resume-past-max → `HaltError`. Preserve `return phase_session_id` on the `done`/skip early exits and `return planner_reviewer.session_id` on completion.

- [x] **Task 4: Point `_implement_loop` / `_test_loop` at the unified processor** (depends on Task 3)
  Files: `orchestrator/main.py`
  Update the two loop wrappers to build their `Mode` and call the single `process_milestone`:
  - `_implement_loop(project_dir, config, planner_prompt_name="planner", roadmap_filename="ROADMAP.md")` keeps its params (the implement variant passes non-defaults) and constructs an implement `Mode` from them — `IMPLEMENT_MODE._replace(planner_prompt_name=planner_prompt_name, roadmap_filename=roadmap_filename)` (valid because `Mode` is a `NamedTuple`, Task 1) so callers passing non-default prompt/roadmap still work — then its lambda calls `process_milestone(project_dir, m, i, config, mode, phase_session_id=sid)` with `mode` passed explicitly.
  - `_test_loop` builds `TEST_MODE` and its lambda calls the same unified `process_milestone`.
  Delete `process_test_milestone`, `_detect_test_milestone_step`'s body-duplication is already handled in Task 2 (wrapper retained). Confirm no remaining references to `process_test_milestone` exist anywhere in `main.py`. Do not touch `agents.py`, `notify.py`, prompts, or the on-disk artifact protocol.

## Verify (manual, not a task)
Run `uv run pytest` — must stay green with zero assertion changes. Spot-check that resume from every `step` (`plan`, `planned`, `plan_review_failed:N`, `plan_reviewed`, `implemented`, `review`/`test_run` mid-loop, `review_failed:N`/`test_run_failed:N`, `done`) dispatches identically in both modes, and that artifact filenames, sidecar `step` strings, and print lines are byte-for-byte unchanged.
