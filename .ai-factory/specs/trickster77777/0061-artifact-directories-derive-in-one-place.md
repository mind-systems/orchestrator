# Artifact directories derive in one place

**Date:** 2026-10-05
**Source:** the user's go in chat on 2026-10-05 for closing "one choice held twice" by design, under `.ai-factory/ARCHITECTURE.md`

Governing spec: [ARCHITECTURE.md](../../ARCHITECTURE.md) — § What varies (Layout), § Composition root; layout is described on [named-roadmaps.md](../../../docs/features/named-roadmaps.md).

What diverges now: [.ai-factory/specs/trickster77777/0059-the-verify-step-is-chosen-at-assembly.md](0059-the-verify-step-is-chosen-at-assembly.md).

## What is true now

This is the tree as the verify-kind task leaves it: `Mode` holds the verify kind as `verify`, and the output directory's name is `mode.verify.output_dirname`.

The per-roadmap artifact subdirectory is `Mode.artifact_subdir` (`str | None`, `None` for the default flat pair). `_artifact_subdir(relpath: str) -> str | None` in `orchestrator/main.py` derives it from the roadmap path; `_implement_loop` and `_test_loop` call it once and set it on the mode with `_replace(...)`.

It is then joined onto artifact directories by hand, in `process_task` and in `_run_dynamic_loop`:

- `process_task` builds `plans_dir` (`.ai-factory/plans`), `output_dir` (`.ai-factory/` plus `mode.verify.output_dirname`) and `plan_reviews_dir` (`.ai-factory/plan-reviews`), then, when `mode.artifact_subdir` is set, joins it onto `plans_dir`, `output_dir` and `plan_reviews_dir`. Its `mkdir(parents=True, exist_ok=True)` calls follow.
- `_run_dynamic_loop(project_dir, roadmap_path, config, process_fn, artifact_subdir: str | None = None)` builds `.ai-factory/plans` itself, joins its `artifact_subdir` argument onto it when set, creates that directory, and reads it for `_next_number`. `_implement_loop` and `_test_loop` pass `artifact_subdir=mode.artifact_subdir`.

No module other than `main.py` builds an artifact directory.

## What must be true after

**The function.** `_artifact_dir(project_dir: Path, mode: Mode, dirname: str) -> Path` in `main.py` returns `project_dir / ".ai-factory" / dirname`, joined with `mode.artifact_subdir` when that is set.

**`process_task`** gets its plans, output (`mode.verify.output_dirname`) and plan-reviews directories from `_artifact_dir`. Its `mkdir` calls stay as they are.

**`_run_dynamic_loop`** takes `mode: Mode` in place of its `artifact_subdir` parameter and gets its plans directory from `_artifact_dir`. It still creates only the plans directory. `_implement_loop` and `_test_loop` pass the mode.

**The test**, in `tests/test_main.py`: `_artifact_dir` returns `.ai-factory/plans` under the project directory for a mode without a subdirectory, `.ai-factory/plans/john-doe` when `artifact_subdir="john-doe"`, and `.ai-factory/test-runs` for `TEST_MODE.verify.output_dirname`, which is `test-runs`. A wrong join writes a named roadmap's artifacts into the shared flat directory, where they share a numbering axis with the default pair's, and nothing fails: the run proceeds with plans numbered against the wrong set. That is the silent failure the test is for.

The change is behaviour-neutral, including when directories get created.

## What breaks on contact

- The `artifact_subdir` parameter of `_run_dynamic_loop` is replaced by `mode`; its callers, `_implement_loop` and `_test_loop`, change with it. No test calls `_run_dynamic_loop`.
- `_artifact_subdir` and its tests are unchanged.
- `_artifact_dir` takes `Mode`, which `main.py` already defines; `process_task` and `_run_dynamic_loop` read the artifact subdirectory from the mode and nowhere else.
