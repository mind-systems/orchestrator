# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
cd orchestrator && uv sync

# Config file (required before first run)
cp orchestrator.json.example orchestrator.json  # edit as needed

# Plan + implement milestones (no review pass)
uv run orchestrator implement /path/to/project

# Write tests for milestones from ROADMAP_TESTS.md
uv run orchestrator test /path/to/project

# Default (implement) on current directory
uv run orchestrator
```

No test suite or linter is configured.

## Documentation

| Doc | What it covers |
|-----|----------------|
| [Рабочий процесс](docs/workflow.md) | The established working pattern: roadmap filling → implement → test coverage → prune |
| [Как это работает](docs/how-it-works.md) | Agent pipeline mechanics, sessions, resume after interruption, file protocol, signals |
| [Модель контекста](docs/context-model.md) | The agent's perception tree: what is passed literally, what is lifted by following edges (Spec: notes, roadmap neighbors, CLAUDE.md), eager vs lazy graph loading |
| [Когда цикл не сходится](docs/non-convergence.md) | The two terminal-stop patterns (convergence without a signature vs escalation around one blocker), how to read review tails, resolutions outside the loop |
| [Режим тестирования](docs/test-mode.md) | Writing tests through the orchestrator; real test runs as the final check |
| [Конфигурация](docs/configuration.md) | Config file, agent models, iteration limits, usage thresholds |
| [Фазовые сессии](docs/phase-sessions.md) | Token economics: resume vs live process measurements, why `enable_phase_sessions` defaults to `false` |
| [Требования к проекту](docs/target-project.md) | What a target project needs to be orchestratable |

## Architecture

Four-agent pipeline that processes milestones from a target project's `.ai-factory/ROADMAP.md`:

1. **PlannerReviewer** (`agents.py`) — Opus/high. Session-persistent. Writes the plan, then later reviews code changes in the same session (so the reviewer has full planner context).
2. **PlanReviewer** (`agents.py`) — Opus/high. Fresh session per attempt. Reviews the plan *before* implementation starts, writes `PLAN_REVIEW_PASS` or findings to `.ai-factory/plan-reviews/`.
3. **Implementer** (`agents.py`) — Sonnet/high. Session-persistent across implement → fix iterations.
4. **TestRunner** (`agents.py`) — No LLM. Used only in `test` mode: reads `## Test Command` from the plan file, runs it via shell, writes stdout+exit code to `.ai-factory/test-runs/`. Returns `True` if exit code is 0.

Pipeline per milestone (`implement` mode):

```
PlannerReviewer.plan()
  └─► PlanReviewer.review_plan()  ×N  (FAIL → PlannerReviewer.plan() again)
        └─► Implementer.implement()
              └─► PlannerReviewer.review()  ×N  (FAIL → Implementer.implement() again)
                    └─► mark_done() + git commit
```

Pipeline per milestone (`test` mode):

```
PlannerReviewer.plan()      ← uses test-planner prompt
  └─► PlanReviewer.review_plan()  ×N  (FAIL → PlannerReviewer.plan() again)
        └─► Implementer.implement()
              └─► TestRunner.run()  ×N  (FAIL → Implementer.implement() again)
                    └─► mark_done() + git commit
```

All agents communicate through files, not shared memory. Output directories under `.ai-factory/`: `plans/`, `plan-reviews/`, `reviews/`, `patches/`, `test-runs/`.

`_run_claude()` in `agents.py` shells out to the `claude` CLI with `--output-format stream-json` and parses `result`/`session_id`. Pass/fail is detected by `PLAN_REVIEW_PASS` (plan review) or `REVIEW_PASS` (code review) as the last line of the respective file.

## Target project requirements

The project being orchestrated must have:
- `.ai-factory/ROADMAP.md` with milestones formatted as:
  ```
  - [ ] **Title** — Description
  ```
- `.ai-factory/DESCRIPTION.md` — tech stack and conventions (read by the planner agent)
- An initialized git repo (the orchestrator commits after each milestone)

For `test` mode, milestones are read from `.ai-factory/ROADMAP_TESTS.md` (same format). This file is separate from `ROADMAP.md` so test tasks don't pollute the main roadmap.

## Key constants

- `orchestrator.json` config file (project root, gitignored — copy from `orchestrator.json.example`):
  - `max_iterations` (default 3) — single iteration limit for all flows (plan review, implement review, test run)
  - `usage_threshold_5h` (default 90) — stop if 5-hour session usage exceeds this percentage
  - `usage_threshold_weekly` (default 95) — stop if weekly usage exceeds this percentage
  - `enable_phase_sessions` (default false) — carry PlannerReviewer session across milestones within a roadmap phase
- `ORCHESTRATOR_CONFIG` env var — override the config file path (default: `orchestrator.json` in the project root)
- Default models/effort: PlannerReviewer=opus/high, PlanReviewer=opus/high, Implementer=sonnet/high — override when instantiating agents in `process_milestone()`
