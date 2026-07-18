# Plan: 6.1 — User-facing runtime surface speaks `task`

## Context
Rename the last user-facing surface — Telegram alert tokens + message text, console prose, CLI `--help`, and the `runtime.py` run-summary — from `milestone` to `task`, so the operator meets the reserved word `task` coherently at run time. Post-5.1, only string literals and alert tokens change; no Python identifier is touched.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Assumptions / scope notes
- **5.1 has landed** (verified): `notify.py` comments already say "task failure", `state.tasks_done` exists, and every call site already reads `task.title` / `task.slug`. Only string literals and alert tokens remain in `milestone` form. If any line still shows a `milestone`-shaped *identifier*, that is a 5.1 gap to flag — not something this task renames.
- **The whole milestone lands as one git commit** (the orchestrator commits `git add -A` once per completed task). Slice 1's spec-mandated indivisibility ("`_FAIL_ALERTS`, the call-site tokens, and both config files' token values change together — never partially") is therefore satisfied by construction; no multi-commit split, and no Commit Plan.
- **Live `orchestrator.json` scope:** per the spec guard, in the repo-root `orchestrator.json` touch **only** the `telegram_alerts` array's string values (line 8). Leave every other key byte-for-byte — including the separate `telegram_alerts_example_all` key (line 9), which the spec does not list for the live file. Never touch `telegram_bot_token`, `telegram_chat_id`, or any other credential/key.
- The `"stop"` and `"done"` alert tokens are out of scope and stay unchanged.
- Do not touch `docs/*.md`, `CLAUDE.md`, `README.md`, `ARCHITECTURE.md`, or the prompt bodies (`planner.md` / `test-planner.md` / `reviewer.md`) — later phases own those.

## Tasks

### Phase 1: Alert tokens + config (indivisible slice — silent-failure risk if split)

- [x] **Task 1: Rename alert tokens and message text in source + config**
  Files: `orchestrator/notify.py`, `orchestrator/main.py`, `orchestrator.json.example`, `orchestrator.json`
  All four move together as one unit — if any moves without the others a real failure renders the wrong emoji or an alert stops firing silently.
  - `notify.py:15`: `_FAIL_ALERTS = {"milestone-fail"}` → `_FAIL_ALERTS = {"task-fail"}`. (Comments on lines 14/17 already read "task failure" post-5.1 — verify, do not re-edit.)
  - `main.py:241` and `main.py:359` (success call sites): `notify(config, f"{project_dir.name}: Milestone done: {task.title}", "milestone")` → `... Task done: {task.title}", "task")` — both the message text *and* the token.
  - `main.py:505` (failure call site): `"milestone-fail"` → `"task-fail"`.
  - `orchestrator.json.example:11`: `"telegram_alerts_example_all": ["milestone-fail", "stop", "milestone", "done"]` → `["task-fail", "stop", "task", "done"]`.
  - `orchestrator.json:8`: in the `telegram_alerts` array only, `"milestone-fail"` → `"task-fail"` (and any bare `"milestone"` → `"task"`). Leave line 9 (`telegram_alerts_example_all`) and every other key untouched.

- [x] **Task 2: Update token tests in lockstep** (depends on Task 1)
  Files: `tests/test_notify.py`, `tests/test_main.py`, `tests/test_config.py`
  - `test_notify.py:38`: `ALL_ALERTS = ["milestone-fail", "stop", "milestone", "done", "whatever"]` → `["task-fail", "stop", "task", "done", "whatever"]`.
  - `test_notify.py`: rename `test_milestone_fail_alert_prefixed_red` → `test_task_fail_alert_prefixed_red` (line ~41) and `test_milestone_alert_prefixed_green` → `test_task_alert_prefixed_green` (line ~55); update their docstrings and the `notify(config, "some message", "milestone-fail"/"milestone")` token args to `"task-fail"`/`"task"`. Update `_config(["milestone"])` at line ~83 → `_config(["task"])`.
  - `test_main.py`: rename `test_cli_pipeline_stop_error_routes_to_milestone_fail` (line 848) → `test_cli_pipeline_stop_error_routes_to_task_fail`; update its docstring (line 849) and `assert recorded[-1][1] == "milestone-fail"` (line 853) → `== "task-fail"`.
  - `test_config.py`: `_write_override(project_dir, {"telegram_alerts": ["milestone-fail"]})` (line 111) and `assert config.telegram_alerts == ["milestone-fail"]` (line 115) → `["task-fail"]`.

### Phase 2: Display prose (non-breaking)

- [x] **Task 3: Rename display prose in `main.py` and `runtime.py`** (depends on Task 1)
  Files: `orchestrator/main.py`, `orchestrator/runtime.py`
  - `main.py:44`: `header_label="MILESTONE"` → `"TASK"`; `main.py:60`: `header_label="TEST MILESTONE"` → `"TEST TASK"`.
  - `main.py:51`: skip_message `"...(milestone may already be done). Skipping."` → `"...(task may already be done). Skipping."`.
  - `main.py:243` and `main.py:362`: `print(f">>> Milestone done [...]")` → `print(f">>> Task done [...]")`.
  - `main.py:311`: `PipelineStopError(f"No passing plan review found for milestone {seq}-{task.slug}...")` → `"...found for task {seq}-{task.slug}..."`.
  - `main.py:378`: `print("All milestones are done!")` → `print("All tasks are done!")`.
  - `main.py:382`/`384`: pending-count prints — `"Found N pending milestones out of ... total (... N milestones after marker not queued)."` and `"Found N pending milestones out of N total."` → `milestones` → `tasks` in both (keep shape/format args intact).
  - `main.py:394`: `f"All milestones done: {project_dir.name}\n{_run_summary()}"` → `f"All tasks done: ..."`.
  - `main.py:401-402`: `PipelineStopError(f"Milestone '{task.title}' checkbox is still unchecked... Refusing to re-run the same milestone forever...")` → `"Task '{task.title}' checkbox... same task forever..."`.
  - `main.py:484-485`: argparse `help=` strings `"Plan and implement milestones"` → `"Plan and implement tasks"`, `"Write tests for milestones (uses test-planner prompt)"` → `"Write tests for tasks (uses test-planner prompt)"`.
  - `runtime.py:23`: `print("\n>>> Will stop after the current milestone finishes. ...")` → `"...current task finishes. ..."`.
  - `runtime.py:39`: `f"Ran for {_run_elapsed()} · {state.tasks_done} milestones done"` → `"... {state.tasks_done} tasks done"` (identifier `state.tasks_done` already renamed by 5.1 — only the trailing string word changes).

- [x] **Task 4: Update prose tests in lockstep** (depends on Task 3)
  Files: `tests/test_runtime.py`
  - Lines ~17, 24, 30, 35: docstrings and assertions `" · 3 milestones done"` / `"Ran for unknown · 0 milestones done"` → `"... tasks done"` throughout.
  - Line ~167: `assert "Will stop after the current milestone finishes." in out` → `"Will stop after the current task finishes."`.

### Phase 3: Verify

- [x] **Task 5: Run the suite and the acceptance grep** (depends on Tasks 1–4)
  Files: (none — verification only)
  - `uv run pytest` → green.
  - `grep -rn "milestone" orchestrator/*.py tests/*.py` → **zero hits.** (The config JSON files are intentionally outside this grep; `telegram_alerts_example_all` in the live `orchestrator.json` is deliberately left per the spec guard.)
