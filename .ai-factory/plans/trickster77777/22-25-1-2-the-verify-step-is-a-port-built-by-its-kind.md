# Plan: 25.1.2 — the verify step is a port, built by its kind

## Context
Today `process_task` (`orchestrator/main.py`) builds a `TestRunner` only when `mode.verify.step == "test_run"` and chooses between `TestRunner.run` and `PlannerReviewer.review` in a local `_verify` closure. That means the flow asks which mode it is in, which the architecture rule forbids. This task adds the `VerifierProtocol` port and gives `VerifyKind` a `make_verifier` factory, so the flow calls whatever the kind builds. It changes no behaviour: no artifact name, sidecar step value, completion signal or outcome changes. Governing spec: `.ai-factory/ARCHITECTURE.md` (§ What varies, § Composition root, § The rule). Task spec: `.ai-factory/specs/trickster77777/0060-the-verify-step-is-a-port-chosen-with-the-mode.md`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### The port and its implementations (`agents.py`)

- [x] **Define the verify port**
  Files: `orchestrator/agents.py`
  Widen the `typing` import from `NamedTuple` to `Callable, NamedTuple, Protocol`. Directly above `class VerifyKind(NamedTuple)`, add `class VerifierProtocol(Protocol)` with a one-line docstring (given the plan and output path, write the verify artifact and report pass or fail by its completion signal). It has exactly one method:
  `def verify(self, plan_path: Path, out_path: Path, prev_out_path: Path | None) -> bool: ...`

- [x] **PlannerReviewer implements the port** (depends on Define the verify port)
  Files: `orchestrator/agents.py`
  Directly after `PlannerReviewer.review`, add `def verify(self, plan_path: Path, out_path: Path, prev_out_path: Path | None) -> bool:` that returns `self.review(plan_path, out_path, prev_review_path=prev_out_path)`. Leave `review` unchanged.

- [x] **TestRunner implements the port** (depends on Define the verify port)
  Files: `orchestrator/agents.py`
  Add a class attribute `__test__ = False` with a short comment saying it is not a pytest test class. `tests/test_agents.py` imports `TestRunner`, so pytest tries to collect it, and once the class has a constructor pytest emits `PytestCollectionWarning: cannot collect test class 'TestRunner' because it has a __init__ constructor`. Add `def __init__(self, project_dir: Path) -> None:` that stores `self.project_dir = project_dir`. Rename `run(self, plan_path, output_path, project_dir)` to `verify(self, plan_path: Path, out_path: Path, prev_out_path: Path | None) -> bool`. Keep the body as it is, with two changes: every `output_path` becomes `out_path`, and `cwd=str(project_dir)` becomes `cwd=str(self.project_dir)`. `prev_out_path` stays unused. Keep `_extract_test_command` a `@staticmethod`, unchanged, because `tests/test_agents.py` calls it on the class.

- [x] **VerifyKind carries its factory** (depends on PlannerReviewer implements the port, TestRunner implements the port)
  Files: `orchestrator/agents.py`
  - Append a last field with no default to `VerifyKind`: `make_verifier: Callable[[PlannerReviewer, Path], VerifierProtocol]  # (planner_reviewer, project_dir) -> verifier`. This forward reference is safe because the module has `from __future__ import annotations`.
  - Between the `VerifyKind` class and the `REVIEW_VERIFY` instance, add two module-level functions. They must be defined before the instances that reference them:
    - `_review_verifier(planner_reviewer: PlannerReviewer, project_dir: Path) -> VerifierProtocol`: returns `planner_reviewer`.
    - `_test_run_verifier(planner_reviewer: PlannerReviewer, project_dir: Path) -> VerifierProtocol`: returns `TestRunner(project_dir)`. `TestRunner` is defined later in the module, but the name is only looked up when the function is called.
  - Add `make_verifier=_review_verifier` as the last keyword to `REVIEW_VERIFY`, and `make_verifier=_test_run_verifier` to `TEST_RUN_VERIFY`. Every other value stays the same.

### The flow (`main.py`)

- [x] **process_task calls what the kind builds** (depends on VerifyKind carries its factory)
  Files: `orchestrator/main.py`
  - Import line from `.agents`: remove `TestRunner`. The other names stay.
  - After `implementer = Implementer(project_dir)`, replace the `test_runner = ...` line and the whole `_verify` closure with `verifier = mode.verify.make_verifier(planner_reviewer, project_dir)`. This keeps the verifier built after agent construction, which comes after the `escalated`/`done` early returns, so `test_process_task_escalated_sidecar_raises_without_constructing_agents` still holds.
  - In the implement → verify loop, drop the `mode.verify.step == "review" and` condition from the previous-output lookup. For every mode, when `iteration > 1` and the previous output file (`output_suffix` formatted with `n=iteration - 1`) exists, pass it as `prev_out_path`; otherwise pass `None`. Replace `passed = _verify(out_path, prev_out_path)` with `passed = verifier.verify(plan_path, out_path, prev_out_path)`.
  - Do not touch `step == mode.verify.step` or `step in ("implement", mode.verify.step)`. These compare the resume step to the kind's step name and do not compare `mode.verify.step` to a literal. After this edit, `grep -n 'mode.verify.step ==' orchestrator/main.py` must find no comparison against a string literal.
  - Neutrality check: the test-run kind now also receives `prev_out_path` on iterations after the first, but `TestRunner.verify` ignores it, so its behaviour is unchanged. The review kind gets exactly the value it gets today.

- [x] **Verify nothing else references the old surface** (depends on process_task calls what the kind builds)
  Files: `orchestrator/`, `tests/`, `docs/`
  Run `grep -rn --include='*.py' --include='*.md' "TestRunner()\|\.run(plan_path\|_verify(\|test_runner" orchestrator tests docs`. The include filters keep stale `__pycache__/*.pyc` bytecode out of the search, which would otherwise match. It must find no remaining references. `docs/features/test-mode.md` already names `TestRunner.verify()`, so no doc changes. Run `uv run pytest` and confirm the existing suite passes with no warnings. The baseline is 224 passed and 0 warnings, and a `PytestCollectionWarning` for `TestRunner` means `__test__ = False` is missing. No test is added.
