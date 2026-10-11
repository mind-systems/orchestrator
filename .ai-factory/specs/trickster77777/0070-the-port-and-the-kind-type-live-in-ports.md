# The port and the kind type live in ports.py

**Date:** 2026-10-11
**Source:** the user's go in chat on 2026-10-11, «давай декомпоуз 29» and «ставим и сохраняем»

Governing spec: [ARCHITECTURE.md](../../ARCHITECTURE.md) — § Dependency Rules and § Folder Structure.

What diverges now: [.ai-factory/specs/trickster77777/0067-modules-do-not-yet-follow-the-layer-map.md](0067-modules-do-not-yet-follow-the-layer-map.md).

## What is true now

This is the tree as the tasks "the outcome exceptions live in `errors.py`" and "the file protocol lives in `protocol.py`" leave it.

`orchestrator/agents.py` defines:

- `VerifierProtocol(Protocol)` with `verify(self, plan_path: Path, out_path: Path, prev_out_path: Path | None) -> bool`;
- `VerifyKind(NamedTuple)` with the fields `step`, `fail_tag`, `output_dirname`, `output_suffix`, `pass_signal`, `running_header`, `pass_line_label`, `fail_line_label`, `max_iterations_message` and `make_verifier: Callable[[PlannerReviewer, Path], VerifierProtocol]`, annotated with the role `PlannerReviewer`;
- `_review_verifier(planner_reviewer: PlannerReviewer, project_dir: Path) -> VerifierProtocol`, `_test_run_verifier(planner_reviewer: PlannerReviewer, project_dir: Path) -> VerifierProtocol`, and the instances `REVIEW_VERIFY` and `TEST_RUN_VERIFY`.

`main.py` imports `VerifyKind`, `REVIEW_VERIFY` and `TEST_RUN_VERIFY` from `agents`. `resume.py` imports `REVIEW_VERIFY`, `TEST_RUN_VERIFY` and `VerifyKind` from `agents` and `_read_sessions` from `protocol`. `_detect_step` takes `verify: VerifyKind`. Its wrappers `_detect_task_step(project_dir, seq, slug, plan_path, plan_reviews_dir, reviews_dir)` and `_detect_test_task_step(project_dir, seq, slug, plan_path, plan_reviews_dir, test_runs_dir)` pass `REVIEW_VERIFY` and `TEST_RUN_VERIFY`; only tests call them, and `tests/test_main.py` imports them from `orchestrator.resume`.

## What must be true after

A new `orchestrator/ports.py` defines `VerifierProtocol` and `VerifyKind`, with `make_verifier: Callable[[VerifierProtocol, Path], VerifierProtocol]`: the reviewer parameter is typed by the port, so `ports` names no role. It imports nothing from the package.

`_review_verifier`, `_test_run_verifier`, `REVIEW_VERIFY` and `TEST_RUN_VERIFY` stay in `agents`, their reviewer parameter typed `VerifierProtocol`. `agents` and `main` import `VerifierProtocol` and `VerifyKind` from `ports`.

`_detect_task_step` and `_detect_test_task_step` leave `resume.py` and become helpers in `tests/test_main.py`, with the same names, signatures and behaviour; they pass `REVIEW_VERIFY` and `TEST_RUN_VERIFY`, imported from `agents`, to `_detect_step`. `resume` imports `VerifyKind` from `ports` and `_read_sessions` from `protocol` only; the `resume` → `agents` edge is gone.

The change is behaviour-neutral: step values, tags, signals and artifact names are as before.

## What breaks on contact

- `tests/test_main.py` imports the wrappers from `orchestrator.resume`; it defines them locally instead, and the `test_detect_task_step_*` and `test_detect_test_task_step_*` tests call those.
- No test patches `VerifyKind`, the port, the factories or the instances; the `process_task` tests run on the default mode.
- A wrapper left importable from `resume` would keep `resume` → `agents` alive through `REVIEW_VERIFY` and `TEST_RUN_VERIFY`.
