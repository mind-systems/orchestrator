# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
cd orchestrator && uv sync

# Config file (required before first run)
cp orchestrator.json.example orchestrator.json  # edit as needed

# Plan + implement milestones
uv run orchestrator implement /path/to/project

# Write tests for milestones from ROADMAP_TESTS.md
uv run orchestrator test /path/to/project

# Default (implement) on current directory
uv run orchestrator

# Run the unit tests
uv run pytest
```

Unit tests live in `tests/` (pytest, a dev dependency) and cover the pure, silent-failure surfaces — roadmap parsing, sidecar step-detection / resume dispatch, and usage-percentage parsing. No linter is configured.

## Documentation

| Doc | What it covers |
|-----|----------------|
| [Workflow](docs/workflow.md) | The established working pattern: roadmap filling → implement → test coverage → prune |
| [How it works](docs/how-it-works.md) | Agent pipeline mechanics, sessions, resume after interruption, file protocol, signals |
| [Context model](docs/context-model.md) | The agent's perception tree: what is passed literally, what is lifted by following edges (Spec: notes, roadmap neighbors, CLAUDE.md), eager vs lazy graph loading |
| [Failures and halts](docs/failures-and-halts.md) | The failure-vs-halt axis: what counts as a milestone failure vs an operational halt, the invariants (bounded attempts, transient absorption, resumability, fail-safe side effects), outcome signalling |
| [Non-convergence](docs/non-convergence.md) | The two terminal-stop patterns (convergence without a signature vs escalation around one blocker), how to read review tails, resolutions outside the loop |
| [Test mode](docs/test-mode.md) | Writing tests through the orchestrator; real test runs as the final check |
| [Configuration](docs/configuration.md) | Config file, agent models, iteration limits, usage thresholds |
| [Migrate to named roadmap](docs/migrate-to-named-roadmap.md) | Step-by-step: switch a project from the shared ROADMAP.md to a user-scoped named roadmap |
| [Phase sessions](docs/phase-sessions.md) | Token economics: resume vs live process measurements, why `enable_phase_sessions` defaults to `false` |
| [Target project](docs/target-project.md) | What a target project needs to be orchestratable |

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

All agents communicate through files, not shared memory. Output directories under `.ai-factory/`: `plans/`, `plan-reviews/`, `reviews/`, `test-runs/`. Flat for the default `ROADMAP.md`/`ROADMAP_TESTS.md` pair; any other (named) roadmap routes its artifacts into a per-roadmap subdirectory keyed by the roadmap file's stem (e.g. `plans/john-doe/`, `reviews/john-doe/`) — see [docs/how-it-works.md](docs/how-it-works.md).

Consumer skills in `~/projects/skills` mirror this file protocol in their `orchestrator-artifacts` engine — any change to the protocol (directory layout, artifact naming, PASS signals, sidecar fields, review-section format) must be reflected there.

`_run_claude()` in `agents.py` shells out to the `claude` CLI with `--output-format stream-json` and parses `result`/`session_id`. Pass/fail is detected by `PLAN_REVIEW_PASS` (plan review) or `REVIEW_PASS` (code review) as the last line of the respective file.

## Target project requirements

What a target project needs (roadmap/milestone format, phases, the `---STOP---` breakpoint, `ARCHITECTURE`/`RULES` files, git) — [docs/target-project.md](docs/target-project.md). The parsing itself lives in `roadmap.py`.

## Configuration

All settings live in `orchestrator.json` (project root, gitignored — copy from `orchestrator.json.example`; path override via `ORCHESTRATOR_CONFIG`). Every key, the agent models, and Telegram alerts — [docs/configuration.md](docs/configuration.md). Defaults are set in `config.py` and when instantiating agents in `process_milestone()`.
