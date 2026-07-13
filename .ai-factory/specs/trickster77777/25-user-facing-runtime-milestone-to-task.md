# User-facing runtime surface speaks `task`

**Date:** 2026-07-14
**Source:** conversation context — editor decomposition of Phase 6, ratified by the architect

## Problem today

Spec 24 (task 5.1) renames every Python identifier, docstring, and comment from `milestone` to `task`, but it explicitly leaves every user-facing string literal untouched. The operator still meets the old word at run time: the Telegram alert tokens (`milestone` / `milestone-fail`), the Telegram message text ("Milestone done: …"), the console prints (the `MILESTONE` header, "All milestones are done!", the pending-count lines), the CLI `--help` text, the exception prose surfaced through `PipelineStopError`, and the `runtime.py` run-summary ("N milestones done"). This task closes that gap — the last surface where the orchestrator still speaks the pre-conformance vocabulary.

**Precondition — 5.1 has already landed.** This task runs after 5.1 in roadmap order and several of the lines it touches are lines 5.1 already rewrote the identifier half of. Every code reference in this spec is written against the **post-5.1** names — `task.title`, `task.slug`, `task.description`, `state.tasks_done`, `process_task`, `mode.header_label`, etc. — never the current on-disk `milestone*` names. On a shared line, this task changes only the string literal or token; the identifier is already `task`-shaped and must not be touched again.

## The change

Two slices. The first is a single indivisible unit (silent-failure risk); the second is plain prose with no external contract.

### 1. Alert tokens + config — breaking, must land as one unit

If any one of these moves without the others, a real pipeline failure either renders with the wrong emoji or a real alert stops firing — silently, no exception. Treat this as one diff:

| File | Current | New |
|---|---|---|
| `notify.py:15` | `_FAIL_ALERTS = {"milestone-fail"}` | `_FAIL_ALERTS = {"task-fail"}` |
| `notify.py:14,17` | comments "…a milestone failure…" / "…not a milestone failure" | "…a task failure…" / "…not a task failure" |
| `main.py` (success `notify()` call sites, ~241 and ~359) | `notify(config, f"{project_dir.name}: Milestone done: {task.title}", "milestone")` | `notify(config, f"{project_dir.name}: Task done: {task.title}", "task")` |
| `main.py` (~505) | `notify(config, ..., "milestone-fail")` | `notify(config, ..., "task-fail")` |
| `orchestrator.json.example` (~line 11) | `"telegram_alerts_example_all": ["milestone-fail", "stop", "milestone", "done"]` | `["task-fail", "stop", "task", "done"]` |
| `orchestrator.json` (repo root, gitignored, live) | `"telegram_alerts": [...]` values `"milestone-fail"` (any `"milestone"`) | `"task-fail"` (`"task"`) — **only the `telegram_alerts` array's values.** Never touch `telegram_bot_token`, `telegram_chat_id`, or any other key. |

Token tests (same indivisible unit — a passing suite is this slice's own proof):

- `test_notify.py`: `ALL_ALERTS` list (~38) values `"milestone-fail"` / `"milestone"` → `"task-fail"` / `"task"`; `_config(["milestone"])` (~83) → `_config(["task"])`; rename `test_milestone_fail_alert_prefixed_red` → `test_task_fail_alert_prefixed_red` and `test_milestone_alert_prefixed_green` → `test_task_alert_prefixed_green`, docstrings and assertion strings updated to match.
- `test_main.py:848,853`: rename `test_cli_pipeline_stop_error_routes_to_milestone_fail` → `test_cli_pipeline_stop_error_routes_to_task_fail`, docstring updated, `assert recorded[-1][1] == "milestone-fail"` → `== "task-fail"`.
- `test_config.py:~111,115`: `_write_override(project_dir, {"telegram_alerts": ["milestone-fail"]})` and `assert config.telegram_alerts == ["milestone-fail"]` → `["task-fail"]`.

### 2. Display prose — non-breaking

| File | Current | New |
|---|---|---|
| `main.py:44,60` | `header_label="MILESTONE"` / `"TEST MILESTONE"` | `"TASK"` / `"TEST TASK"` |
| `main.py:51` | skip_message "...(milestone may already be done)..." | "...(task may already be done)..." |
| `main.py:243,362` | `print(f">>> Milestone done [...]")` | `print(f">>> Task done [...]")` |
| `main.py:378` | `print("All milestones are done!")` | `print("All tasks are done!")` |
| `main.py:382,384` | "Found N pending milestones out of … total (… — N milestones after marker not queued)." / "Found N pending milestones out of N total." | same shape, "milestones" → "tasks" |
| `main.py:394` | `f"All milestones done: {project_dir.name}\n{_run_summary()}"` | `f"All tasks done: {project_dir.name}\n{_run_summary()}"` |
| `main.py:311` | `PipelineStopError(f"No passing plan review found for milestone {seq}-{task.slug}...")` | "...found for task {seq}-{task.slug}..." |
| `main.py:401-402` | `PipelineStopError(f"Milestone '{task.title}' checkbox is still unchecked... same milestone forever...")` | "Task '{task.title}' checkbox... same task forever..." |
| `main.py:484-485` | argparse `help=` "Plan and implement milestones" / "Write tests for milestones (uses test-planner prompt)" | "Plan and implement tasks" / "Write tests for tasks (uses test-planner prompt)" |
| `runtime.py:23` | `print("...Will stop after the current milestone finishes...")` | "...current task finishes..." |
| `runtime.py:39` | `f"...{state.tasks_done} milestones done"` (identifier already renamed by 5.1; only the string survives to this task) | `f"...{state.tasks_done} tasks done"` |

Matching test updates (same non-breaking slice):

- `test_runtime.py:~17,24,30,35`: docstrings and assertions `" · 3 milestones done"` / `"Ran for unknown · 0 milestones done"` → `"tasks done"` throughout.
- `test_runtime.py:~167`: `assert "Will stop after the current milestone finishes." in out` → `"Will stop after the current task finishes."`.

## Guards

- Do **not** touch code identifiers, docstrings, or comments that mirror a renamed identifier — that is spec 24 / task 5.1's surface, already landed by the time this task runs. If a line still shows a `milestone`-shaped identifier, that is a 5.1 gap to flag, not something this task papers over by renaming it here.
- Do **not** rename the `"stop"` or `"done"` alert tokens — out of scope, unaffected by this language pass.
- The `_FAIL_ALERTS` set, the `"task-fail"` call site, and every config token value (`.example` and the live root file) move together, in one diff — never partially. Partial application is the silent-failure mode this spec exists to prevent (see "The change" § 1).
- `orchestrator.json` (repo root): touch only the `telegram_alerts` array's string values. Every other key — `telegram_bot_token`, `telegram_chat_id`, `max_iterations`, `usage_threshold_*`, `enable_phase_sessions`, `roadmap_path` — is untouched, byte-for-byte.
- The Telegram token-vocabulary rename is a narrow, **silent** breaking change: an operator's own `<project>/.ai-factory/orchestrator.json` override that still lists `milestone-fail` under `telegram_alerts` will no longer match `_FAIL_ALERTS`, so alerts for that project stop firing with no error. This is accepted (per the phase's own framing) — not a defect to work around.

## Verify

- `uv run pytest` green — every test in "The change" renamed in lockstep with the source it exercises.
- `grep -rn "milestone" orchestrator/*.py tests/*.py` → **zero hits.** (This is the orchestrator's own acceptance check when it implements this task, after 5.1 has landed — it cannot be run now, since 5.1 hasn't executed yet and the working tree still carries pre-5.1 identifiers.)
- No on-disk artifact format changes (sidecar keys, plan/review filenames) — this task touches only prose, tokens, and the config token vocabulary.

## What NOT to do

- Do **not** rename any Python identifier — that is 5.1's surface, and by the time this task runs it is already done.
- Do **not** touch `orchestrator.json`'s credentials or any key other than `telegram_alerts`.
- Do **not** split the alert-token slice (§1) across multiple commits or partially apply it — `_FAIL_ALERTS`, the call-site tokens, and both config files' token values change together.
- Do **not** touch `docs/*.md`, `CLAUDE.md`, `README.md`, `ARCHITECTURE.md`, or the skill-name references (`milestone-rescue` → `task-rescue`) — that is Phase 8.
- Do **not** touch `planner.md` / `test-planner.md` / `reviewer.md` — that is Phase 7.

## Tests

No new tests. The existing suite (`test_notify.py`, `test_main.py`, `test_runtime.py`, `test_config.py`) already pins every string this task changes; update those assertions, docstrings, and the three token-test function names in lockstep with the source. A rename that breaks a test here means a missed literal, not a needed new test.
