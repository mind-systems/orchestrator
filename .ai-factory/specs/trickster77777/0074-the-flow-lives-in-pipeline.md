# The flow lives in pipeline.py

**Date:** 2026-10-11
**Source:** the user's go in chat on 2026-10-11, «давай декомпоуз 29» and «ставим и сохраняем»

Governing spec: [ARCHITECTURE.md](../../ARCHITECTURE.md) — § Dependency Rules and § Folder Structure.

What diverges now: [.ai-factory/specs/trickster77777/0067-modules-do-not-yet-follow-the-layer-map.md](0067-modules-do-not-yet-follow-the-layer-map.md).

## What is true now

This is the tree as the tasks above it leave it: the exceptions, the protocol, the port and kind type, the CLI runner and the named-roadmap resolution each have their module.

`orchestrator/main.py` still holds the flow beside the composition root and the CLI: `Mode` (a `NamedTuple` with the fields `roadmap_relpath`, `header_label`, `planner_prompt_name`, `skip_message`, `verify: VerifyKind` and `artifact_subdir`), `IMPLEMENT_MODE`, `TEST_MODE`, `_next_number`, `_artifact_dir`, `_git_commit`, `process_task` and `_run_dynamic_loop`. It also holds `_run_loop`, which nothing calls, and `_implement_loop`, `_test_loop`, `run_implement`, `run_test` and `cli`. `pyproject.toml` names `orchestrator.main:cli` as the script entry point.

`tests/test_main.py` imports `IMPLEMENT_MODE`, `TEST_MODE`, `_artifact_dir`, `_next_number` and `process_task` from `main`. `test_process_task_escalated_sidecar_raises_without_constructing_agents` patches `main_module.PlannerReviewer`, `Implementer`, `PlanReviewer`, `mark_done` and `_git_commit`. The `cli` tests go through `_run_cli_with`, which patches `main_module.load_config`, `run_implement` and `report`.

## What must be true after

A new `orchestrator/pipeline.py` defines `Mode`, `IMPLEMENT_MODE`, `TEST_MODE`, `_next_number`, `_artifact_dir`, `_git_commit`, `process_task` and `_run_dynamic_loop`, bodies unchanged. `_run_loop` is removed from `main.py` because nothing calls it. From the package it imports the roles from `agents`, `_detect_step` from `resume` (the named `pipeline` → `resume` edge), and `VerifyKind` from `ports`, together with `errors`, `protocol`, `roadmap`, `config`, `notify`, `runtime`, `usage` and `state`.

`main` keeps `_implement_loop`, `_test_loop`, `run_implement`, `run_test` and `cli`, imports `IMPLEMENT_MODE`, `TEST_MODE` and `_run_dynamic_loop` from `pipeline`, and stays the `orchestrator.main:cli` entry point. Nothing imports `main`. The tests import the flow from `pipeline`, and their patches on `main_module` for names the flow looks up become patches on `pipeline`.

The change is behaviour-neutral: the loops, artifacts, sidecar steps and outcomes are as before.

On the round it passes the task — and only then — the reviewer reads `../skills/.ai-factory/architects/trickster77777/07/address.md`, relative to this repository's root, at send time, and sends one `SendMessage` to the bare session name on its `session-name:` line, just before writing `REVIEW_PASS`. A review round that does not pass sends nothing. The message says: it is from the orchestrator's run; Phase 29 has landed and the modules follow `ARCHITECTURE.md`'s layer map; skills references now name old homes — `skills/src/skills/orchestrator-artifacts/SKILL.md` ("mirrors the orchestrator's file protocol (`orchestrator/main.py`, …") and `skills/docs/the-pipeline-speaks-to-an-architect.md` ("Read in `orchestrator/orchestrator/agents.py`"), whose launch flags now live in `claude_cli.py`; and no reply is expected. The review file records the tool's result verbatim above `REVIEW_PASS`, which stays the file's last line. If `SendMessage` is unavailable or the send fails, the review file records that and the review still passes; no `ESCALATION`.

## What breaks on contact

- The patches in `test_process_task_escalated_sidecar_raises_without_constructing_agents` move to `pipeline`. Left on `main`, `PlannerReviewer`, `Implementer`, `PlanReviewer`, `mark_done` and `_git_commit` no longer exist there, so each raises `AttributeError`.
- The patches on `main_module.load_config`, `run_implement` and `report` in `_run_cli_with` stay valid: `cli` stays in `main` and looks them up in its own module. No `process_task` test patches `report`.
- `main` no longer imports `subprocess`; the resolution tests that patched `main_module.subprocess` have already moved to `layout`.
- The entry point `orchestrator.main:cli` and `python -m orchestrator.main` are unchanged.
