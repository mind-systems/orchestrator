# Plan: 25.1.1 — the verify kind is one record

## Context
Today a mode's verify choice is spread across several places that nothing keeps in agreement: sibling `Mode` fields in `main.py`, loose strings passed to `_detect_step`, literals in `resume.py`'s wrappers, and pass-signal literals in `PlannerReviewer.review` and `TestRunner.run`. This task gathers the choice into one `VerifyKind` record in `agents.py`, with two instances (`REVIEW_VERIFY`, `TEST_RUN_VERIFY`). The mode holds one kind, `_detect_step` takes it, and the implementations read their pass signal from it. The change is behaviour-neutral: every printed string, sidecar value, artifact name and signal stays byte-identical. The target state is set by `.ai-factory/specs/trickster77777/0062-the-verify-kind-is-one-record.md`, under `.ai-factory/ARCHITECTURE.md` § What varies / § The rule.

Out of scope, because later tasks own them: removing the `mode.verify.step == "test_run"` / `== "review"` comparisons and the `_verify` closure in `process_task` (25.1.2), the hand-joined artifact subdirectories (25.2), and the `PLAN_REVIEW_PASS` literals and `endswith` readers (Phase 26).

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### The record

- [x] **Add `VerifyKind` and its two instances to `agents.py`**
  Files: `orchestrator/agents.py`
  - Add `from typing import NamedTuple` to the stdlib imports.
  - Directly above `class PlannerReviewer`, so the record sits beside its implementations, define `class VerifyKind(NamedTuple)`. Give it a short docstring saying it holds everything that depends on the verify choice. Its fields, in exactly this order and all without defaults, are: `step: str`, `fail_tag: str`, `output_dirname: str`, `output_suffix: str`, `pass_signal: str`, `running_header: str`, `pass_line_label: str`, `fail_line_label: str`, `max_iterations_message: str`. Move the two inline comments now on `Mode` onto the matching fields:
    - `output_suffix`: artifact tail with an `{n}` placeholder
    - `max_iterations_message`: template with `{n}`, `{path}`, `{content}` placeholders
  - Right after the class, define the two instances with keyword arguments. Copy the values verbatim from today's `IMPLEMENT_MODE` / `TEST_MODE` in `main.py`:
    - `REVIEW_VERIFY = VerifyKind(step="review", fail_tag="review_failed:", output_dirname="reviews", output_suffix="-review-{n}.md", pass_signal="REVIEW_PASS", running_header="REVIEWING", pass_line_label="REVIEW PASSED", fail_line_label="Review found issues", max_iterations_message="Implement failed\n\nLast review: {path}\n\n{content}")`
    - `TEST_RUN_VERIFY = VerifyKind(step="test_run", fail_tag="test_run_failed:", output_dirname="test-runs", output_suffix="-test-{n}.txt", pass_signal="TEST_PASS", running_header="RUNNING TESTS", pass_line_label="TESTS PASSED", fail_line_label="Tests failed", max_iterations_message="Test failed\n\nLast run: {path}\n\n{content}")`
  - `agents.py` must not import `main` or `resume`.

- [x] **Make the implementations read their pass signal from their kind** (depends on Add `VerifyKind` and its two instances to `agents.py`)
  Files: `orchestrator/agents.py`
  - In `PlannerReviewer.review`, both prompt sentences now say `end the review file with REVIEW_PASS on its own line` (one in the re-review branch, one in the first-review branch). Change each to interpolate `{REVIEW_VERIFY.pass_signal}` in place of the literal. The rendered text must stay identical.
  - Change the final `return _has_signal(review_text, "REVIEW_PASS")` to `return _has_signal(review_text, REVIEW_VERIFY.pass_signal)`.
  - Update the comment above the check, `# Check the review file, not the chat output — look for REVIEW_PASS on its own line`, so it names the kind's pass signal instead of the literal.
  - In `TestRunner.run`, change `output += "\nTEST_PASS"` to `output += f"\n{TEST_RUN_VERIFY.pass_signal}"`.
  - Leave `PlanReviewer`'s `PLAN_REVIEW_PASS` and all prompt files under `orchestrator/prompts/` untouched. The prompt files keep the protocol literal.

### The mode record

- [x] **`Mode` holds one `verify` kind** (depends on Add `VerifyKind` and its two instances to `agents.py`)
  Files: `orchestrator/main.py`
  - Extend the `from .agents import ...` line with `REVIEW_VERIFY`, `TEST_RUN_VERIFY` and `VerifyKind`. Keep `from typing import NamedTuple`, because `Mode` still uses it.
  - In `class Mode`, remove these fields along with their inline comments: `output_dirname`, `output_suffix`, `verify_step`, `verify_fail_tag`, `pass_signal`, `verify_running_header`, `pass_line_label`, `fail_line_label`, `max_iterations_message`. Add `verify: VerifyKind` as the last field before `artifact_subdir`, with no default. The remaining field order is then `roadmap_relpath`, `header_label`, `planner_prompt_name`, `skip_message`, `verify`, `artifact_subdir`.
  - In `IMPLEMENT_MODE`, drop the moved keyword arguments and add `verify=REVIEW_VERIFY`. In `TEST_MODE`, drop them and add `verify=TEST_RUN_VERIFY`. Their `roadmap_relpath`, `header_label`, `planner_prompt_name` and `skip_message` values stay as they are.
  - The `_replace(...)` calls in `_implement_loop` / `_test_loop` touch only `roadmap_relpath`, `planner_prompt_name` and `artifact_subdir`, so they need no change.

- [x] **`process_task` reads every verify value from `mode.verify`** (depends on `Mode` holds one `verify` kind)
  Files: `orchestrator/main.py`
  Rewrite every use of a moved field inside `process_task` as `mode.verify.<field>`:
  - `output_dir = ai_factory / mode.output_dirname` becomes `mode.verify.output_dirname`.
  - The `_detect_step(...)` call passes `mode.verify` as one argument, replacing the four loose strings (`mode.verify_step, mode.verify_fail_tag, mode.output_suffix, mode.pass_signal`).
  - In `test_runner = TestRunner() if mode.verify_step == "test_run" else None`, use `mode.verify.step`. Keep the literal comparison; replacing it is 25.1.2's job.
  - In `impl_start = counter if step in ("implement", mode.verify_step) else 1` and `if step == mode.verify_step and iteration == counter:`, use `mode.verify.step`.
  - The three `mode.output_suffix.format(...)` uses (feedback path, out path, previous-review path) become `mode.verify.output_suffix.format(...)`.
  - In `if mode.verify_step == "review" and iteration > 1:`, use `mode.verify.step`. Keep the literal for the same reason as above.
  - `mode.verify_running_header` becomes `mode.verify.running_header`. `mode.pass_line_label` becomes `mode.verify.pass_line_label`. `mode.fail_line_label` becomes `mode.verify.fail_line_label`.
  - `mode.verify_fail_tag` (in the `_write_session(..., "step", ...)` call) becomes `mode.verify.fail_tag`. `mode.max_iterations_message` becomes `mode.verify.max_iterations_message`.
  - When done, `grep -n "mode\.\(output_dirname\|output_suffix\|verify_step\|verify_fail_tag\|pass_signal\|verify_running_header\|pass_line_label\|fail_line_label\|max_iterations_message\)" orchestrator/main.py` must return nothing.

### Step detection

- [x] **`_detect_step` takes a `VerifyKind`; the wrappers pass their kind** (depends on Add `VerifyKind` and its two instances to `agents.py`)
  Files: `orchestrator/resume.py`
  - Change `from .agents import _read_sessions` to also import `REVIEW_VERIFY`, `TEST_RUN_VERIFY` and `VerifyKind`. ARCHITECTURE.md's dependency rules allow `resume` → `agents`.
  - In `_detect_step`'s signature, replace `verify_step: str, verify_fail_tag: str, output_suffix: str, pass_signal: str,` with `verify: VerifyKind,`. The positional parameters before it stay as they are.
  - Inside the body:
    - the `_validate_sidecar_step(...)` call passes `verify.fail_tag, verify.output_suffix`. `_validate_sidecar_step`'s own signature (`fail_prefix`, `fail_suffix`) stays as it is.
    - `return (verify_step, n, plan_path)` and `return (verify_step, 1, plan_path)` become `verify.step`.
    - `step_value.startswith(verify_fail_tag)` becomes `verify.fail_tag`.
    - `output_suffix.format(n='*')` becomes `verify.output_suffix.format(n='*')`.
    - `.endswith(pass_signal)` becomes `.endswith(verify.pass_signal)`. Keep `endswith` as it is; Phase 26 owns that.
  - In the docstring's `Steps:` line, change `<verify_step>` to `<verify.step>`.
  - `_detect_task_step` now passes `REVIEW_VERIFY`, and `_detect_test_task_step` passes `TEST_RUN_VERIFY`. Both pass the kind positionally after their output-dir argument and drop the four keyword literals. Their own signatures stay unchanged, since tests call them.
  - Replace each wrapper's docstring line `Literals below mirror main.IMPLEMENT_MODE's ...` / `... main.TEST_MODE's ...` with one that names the kind it passes. For example: "Passes `REVIEW_VERIFY`, the review kind." / "Passes `TEST_RUN_VERIFY`, the test-run kind."
  - Leave the `PLAN_REVIEW_PASS` literals in `resume.py` untouched (Phase 26).

### Verification

- [x] **Confirm the change is behaviour-neutral** (depends on all tasks above)
  Files: none changed
  - Run `uv run pytest` and confirm it passes unchanged. Tests call `_detect_task_step`, `_detect_test_task_step`, `_validate_sidecar_step` and `process_task` with the default mode, and none of those signatures change.
  - Run `uv run python -c "from orchestrator.main import IMPLEMENT_MODE, TEST_MODE; print(IMPLEMENT_MODE.verify.step, TEST_MODE.verify.step)"` and confirm it prints `review test_run`. This proves the import graph has no cycle.
  - Add no tests. A single record makes a mismatched pairing of step, signal and artifact name unrepresentable.
