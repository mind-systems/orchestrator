# The verify kind is one record

**Date:** 2026-10-05
**Source:** the user's go in chat on 2026-10-05 for closing "one choice held twice" by design, under `.ai-factory/ARCHITECTURE.md`

Governing spec: [ARCHITECTURE.md](../../ARCHITECTURE.md) — § What varies (Mode, Verify step), § The rule.

What diverges now: [.ai-factory/specs/trickster77777/0059-the-verify-step-is-chosen-at-assembly.md](0059-the-verify-step-is-chosen-at-assembly.md).

## What is true now

`Mode` (a `NamedTuple` in `orchestrator/main.py`) carries the verify choice as separate sibling fields — `output_dirname`, `output_suffix`, `verify_step`, `verify_fail_tag`, `pass_signal`, `verify_running_header`, `pass_line_label`, `fail_line_label`, `max_iterations_message` — beside its own static fields `roadmap_relpath`, `header_label`, `planner_prompt_name`, `skip_message` and `artifact_subdir: str | None = None`. The mode constants hold these values:

| field | `IMPLEMENT_MODE` | `TEST_MODE` |
|---|---|---|
| `output_dirname` | `"reviews"` | `"test-runs"` |
| `output_suffix` | `"-review-{n}.md"` | `"-test-{n}.txt"` |
| `verify_step` | `"review"` | `"test_run"` |
| `verify_fail_tag` | `"review_failed:"` | `"test_run_failed:"` |
| `pass_signal` | `"REVIEW_PASS"` | `"TEST_PASS"` |
| `verify_running_header` | `"REVIEWING"` | `"RUNNING TESTS"` |
| `pass_line_label` | `"REVIEW PASSED"` | `"TESTS PASSED"` |
| `fail_line_label` | `"Review found issues"` | `"Tests failed"` |
| `max_iterations_message` | `"Implement failed\n\nLast review: {path}\n\n{content}"` | `"Test failed\n\nLast run: {path}\n\n{content}"` |

`process_task` reads each of them from `mode`: the output directory, the artifact names built from `output_suffix`, the running header, the pass and fail lines, the failure tag it writes to the sidecar, the max-iterations message, and `mode.verify_step` in its resume-mid-verify conditions, its `TestRunner` construction and its previous-review lookup.

`_detect_step` in `orchestrator/resume.py` takes the verify choice as loose strings after its paths: `verify_step: str, verify_fail_tag: str, output_suffix: str, pass_signal: str`. `process_task` calls it with `mode.verify_step, mode.verify_fail_tag, mode.output_suffix, mode.pass_signal`. `_detect_task_step` and `_detect_test_task_step` in the same module restate the implement and test values of those strings as literals when they call it, and their docstrings say the literals mirror the mode constants. `_detect_step` hands `verify_fail_tag` and `output_suffix` on to `_validate_sidecar_step`, whose parameters are `fail_prefix` and `fail_suffix`.

In `orchestrator/agents.py`, `PlannerReviewer.review` composes its re-review and its first-review prompt sentences with the literal `REVIEW_PASS` ("end the review file with REVIEW_PASS on its own line") and returns `_has_signal(review_text, "REVIEW_PASS")`. `TestRunner.run` appends `"\nTEST_PASS"` to its output when the exit code is 0.

## What must be true after

**The record.** `VerifyKind(NamedTuple)` in `orchestrator/agents.py` has the fields `step`, `fail_tag`, `output_dirname`, `output_suffix`, `pass_signal`, `running_header`, `pass_line_label`, `fail_line_label` and `max_iterations_message`, in that order, none with a default.

**Its instances**, in `agents.py`:

| field | `REVIEW_VERIFY` | `TEST_RUN_VERIFY` |
|---|---|---|
| `step` | `"review"` | `"test_run"` |
| `fail_tag` | `"review_failed:"` | `"test_run_failed:"` |
| `output_dirname` | `"reviews"` | `"test-runs"` |
| `output_suffix` | `"-review-{n}.md"` | `"-test-{n}.txt"` |
| `pass_signal` | `"REVIEW_PASS"` | `"TEST_PASS"` |
| `running_header` | `"REVIEWING"` | `"RUNNING TESTS"` |
| `pass_line_label` | `"REVIEW PASSED"` | `"TESTS PASSED"` |
| `fail_line_label` | `"Review found issues"` | `"Tests failed"` |
| `max_iterations_message` | `"Implement failed\n\nLast review: {path}\n\n{content}"` | `"Test failed\n\nLast run: {path}\n\n{content}"` |

**The mode record.** `Mode` loses the verify fields listed above and gains `verify: VerifyKind`, declared before `artifact_subdir`, so it carries no default. `IMPLEMENT_MODE` sets `verify=REVIEW_VERIFY` and `TEST_MODE` sets `verify=TEST_RUN_VERIFY`; their other values stay as they are. `process_task` reads every verify value from `mode.verify`.

**Step detection.** `_detect_step` takes `verify: VerifyKind` in place of those loose strings, and reads the step name, failure tag, output suffix and pass signal from it. `_detect_task_step` passes `REVIEW_VERIFY` and `_detect_test_task_step` passes `TEST_RUN_VERIFY`; the wrappers' own signatures stay as they are, and their docstrings name the kind they pass instead of saying literals mirror a mode constant. `_validate_sidecar_step` keeps its signature.

**The implementations read their signal from their kind.** `PlannerReviewer.review` builds its re-review sentence, its first-review sentence and its `_has_signal` check from `REVIEW_VERIFY.pass_signal`, and `TestRunner` appends `TEST_RUN_VERIFY.pass_signal` on a passing run. The prompt files keep the protocol literal.

**Behaviour-neutral.** Every printed string, sidecar value, artifact name and signal stays as it is. No test is added: one record makes a mismatched pairing of step, signal and artifact name unrepresentable.

## What breaks on contact

- `orchestrator/main.py` imports `VerifyKind`, `REVIEW_VERIFY` and `TEST_RUN_VERIFY` from `.agents`, and every use of a moved field in `process_task` becomes `mode.verify.<field>`; `orchestrator/resume.py` imports `VerifyKind`, `REVIEW_VERIFY` and `TEST_RUN_VERIFY` from `.agents` beside `_read_sessions`, which its dependency rules in `ARCHITECTURE.md` allow. `agents.py` imports neither module.
- Tests: grep finds no test that builds a `Mode`, calls `_detect_step`, or reads a moved field. The tests call `_detect_task_step`, `_detect_test_task_step`, `_validate_sidecar_step` and `process_task` (with the default mode), and their signatures are unchanged.
