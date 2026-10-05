# The verify step is a port, built by its kind

**Date:** 2026-10-05
**Source:** the user's go in chat on 2026-10-05 for closing "one choice held twice" by design, under `.ai-factory/ARCHITECTURE.md`

Governing spec: [ARCHITECTURE.md](../../ARCHITECTURE.md) — § What varies (Verify step, Mode), § Composition root, § The rule.

What diverges now: [.ai-factory/specs/trickster77777/0059-the-verify-step-is-chosen-at-assembly.md](0059-the-verify-step-is-chosen-at-assembly.md).

## What is true now

This is the tree as the verify-kind task leaves it: `VerifyKind` exists in `orchestrator/agents.py` with `REVIEW_VERIFY` and `TEST_RUN_VERIFY`, and `Mode` holds one as `verify`.

`process_task` in `orchestrator/main.py` still decides the verify implementation itself, after it constructs `PlannerReviewer` and `Implementer`:

- `test_runner = TestRunner() if mode.verify.step == "test_run" else None`.
- A local closure `_verify(out_path, prev_out_path)` calls `test_runner.run(plan_path, out_path, project_dir)` when `test_runner` is set, and `planner_reviewer.review(plan_path, out_path, prev_review_path=prev_out_path)` otherwise.
- In the implement/verify loop, `prev_out_path` is looked up only when `mode.verify.step == "review"` and `iteration > 1`: the previous output file for that iteration, when it exists.

In `orchestrator/agents.py`:

- `PlannerReviewer.review(self, plan_path: Path, review_path: Path, prev_review_path: Path | None = None) -> bool` writes the review and reports pass or fail by its last-line signal.
- `TestRunner` has no `__init__`. `TestRunner.run(self, plan_path: Path, output_path: Path, project_dir: Path) -> bool` extracts the plan's `## Test Command`, runs it, writes the output and the pass signal, and returns whether the exit code was 0. `_extract_test_command` is a `staticmethod`.
- No port names what the implementations have in common, and `VerifyKind` carries no factory.

## What must be true after

**The port.** `orchestrator/agents.py` defines `VerifierProtocol(typing.Protocol)` with one method:

```python
def verify(self, plan_path: Path, out_path: Path, prev_out_path: Path | None) -> bool: ...
```

**Review implementation.** `PlannerReviewer.verify(plan_path, out_path, prev_out_path)` returns `self.review(plan_path, out_path, prev_review_path=prev_out_path)`. `review` itself is unchanged.

**Test-run implementation.** `TestRunner.__init__(self, project_dir: Path)` stores the project directory. `TestRunner.run` becomes `TestRunner.verify(self, plan_path, out_path, prev_out_path)`: the same body, the project directory taken from `self`, `prev_out_path` unused. `_extract_test_command` stays a `staticmethod`.

**The factory moves onto the kind.** `VerifyKind` gains a field `make_verifier: Callable[[PlannerReviewer, Path], VerifierProtocol]`, where the second argument is the project directory; it is the last field and carries no default. Functions in `agents.py` beside the records back it:

- `_review_verifier(planner_reviewer, project_dir)` returns the `planner_reviewer` it is given.
- `_test_run_verifier(planner_reviewer, project_dir)` returns `TestRunner(project_dir)`.

`REVIEW_VERIFY` sets `make_verifier=_review_verifier` and `TEST_RUN_VERIFY` sets `make_verifier=_test_run_verifier`; their other values stay as they are.

**The flow.** `process_task` builds `verifier = mode.verify.make_verifier(planner_reviewer, project_dir)` after it constructs the agents. The `test_runner` local and the `_verify` closure are gone. For every mode, when `iteration > 1` and the previous output file exists, `process_task` passes that path as `prev_out_path`; otherwise it passes `None`. It calls `verifier.verify(plan_path, out_path, prev_out_path)`. `process_task` compares `mode.verify.step` to no literal; the step name stays as the value used by resume detection and the resume-mid-verify path.

The change is behaviour-neutral: no artifact name, sidecar step value, completion signal or outcome changes. No test is added.

## What breaks on contact

- `TestRunner()` with no argument raises `TypeError`; the construction in `process_task` moves into `_test_run_verifier`.
- `agents.py` imports `Callable` and `Protocol` from `typing`; `main.py` no longer imports `TestRunner`.
- The escalated-sidecar test (`test_process_task_escalated_sidecar_raises_without_constructing_agents`) still holds: the verifier is built after agent construction, and agent construction follows the escalated check.
- The `_extract_test_command` tests in `tests/test_agents.py` are unaffected: it stays a `staticmethod`.
- `docs/features/test-mode.md` already names `TestRunner.verify()`.
