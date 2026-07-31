## Commands

```bash
# Install dependencies
cd orchestrator && uv sync

# Config file (required before first run)
cp orchestrator.json.example orchestrator.json  # edit as needed

# Plan + implement tasks
uv run orchestrator implement /path/to/project

# Write tests for tasks from ROADMAP_TESTS.md
uv run orchestrator test /path/to/project

# Default (implement) on current directory
uv run orchestrator

# Run the unit tests
uv run pytest
```

Unit tests live in `tests/` (pytest, a dev dependency) and cover the pure, silent-failure surfaces — roadmap parsing, sidecar step-detection / resume dispatch, and usage-percentage parsing. No linter is configured.

## Documentation

Documentation follows one placement rule: behaviour lives on its feature's page — the single narrative home, read end to end; a value, a default, or a token literal lives in the reference; the order of calls lives on the spine; meaning and taxonomy — what something means, as opposed to what happens or what a setting is worth — live in the concepts tier; everything else is a link, never a copy. Keep new documentation to this split rather than letting a fact spread across pages again.

| Doc | What it covers |
|-----|----------------|
| **Entry points — start here.** | |
| [Workflow](docs/workflow.md) | The established working pattern: roadmap filling → implement → test coverage → prune |
| [Pipeline](docs/pipeline.md) | Two-phase agent pipeline: sessions, the file protocol, and completion signals |
| **Features — each is a single narrative home for its behaviour.** | |
| [Named roadmaps](docs/features/named-roadmaps.md) | Per-developer roadmaps: the roadmap_path states, artifact routing, and how to migrate |
| [Test mode](docs/features/test-mode.md) | Writing tests through the orchestrator; a real test run as final check |
| [Phase sessions](docs/features/phase-sessions.md) | Token economics behind enable_phase_sessions: resume vs. a live process, measured |
| [Usage limits](docs/features/usage-limits.md) | Session and weekly usage thresholds: when checked, the log line, parse fallback |
| [Resume](docs/features/resume.md) | Resume after an interruption: sidecar contents, the step-value table, plan selection |
| [Escalation](docs/features/escalation.md) | When an agent halts the run for a decision outside its authority |
| **Concepts — what things mean.** | |
| [Context model](docs/concepts/context-model.md) | The agent's perception tree: what's passed literally vs. raised by links |
| [Outcomes](docs/concepts/outcomes.md) | The outcome axis: success, failure, halt, escalation, and their invariants |
| [Non-convergence](docs/concepts/non-convergence.md) | Reading a stalled review loop: three patterns, and how to diagnose them |
| **Reference — values, defaults, and tokens.** | |
| [Target project](docs/reference/target-project.md) | What a target project must provide: roadmap format, phases, breakpoint, ARCHITECTURE/RULES, git |
| [Configuration](docs/reference/configuration.md) | Settings reference: file location, overlay precedence, Telegram credentials and alert colours |

## Architecture

Four-agent pipeline that processes tasks from a target project's `.ai-factory/ROADMAP.md`:

1. **PlannerReviewer** (`agents.py`) — Opus/high. Session-persistent. Writes the plan, then later reviews code changes in the same session (so the reviewer has full planner context).
2. **PlanReviewer** (`agents.py`) — Opus/high. Fresh session per attempt. Reviews the plan *before* implementation starts, writes `PLAN_REVIEW_PASS` or findings to `.ai-factory/plan-reviews/`.
3. **Implementer** (`agents.py`) — Sonnet/high. Session-persistent across implement → fix iterations.
4. **TestRunner** (`agents.py`) — No LLM. Used only in `test` mode: reads `## Test Command` from the plan file, runs it via shell, writes stdout+exit code to `.ai-factory/test-runs/`. Returns `True` if exit code is 0.

Each task runs two bounded phases — plan then plan-review, then implement then review — and ends in `mark_done()` plus a git commit; `test` mode substitutes `TestRunner` for the code review. Stage-by-stage behaviour lives on [docs/pipeline.md](docs/pipeline.md).

All agents communicate through files, not shared memory. Output directories under `.ai-factory/`: `plans/`, `plan-reviews/`, `reviews/`, `test-runs/`. Flat for the default `ROADMAP.md`/`ROADMAP_TESTS.md` pair; any other (named) roadmap routes its artifacts into a per-roadmap subdirectory keyed by the roadmap file's stem (e.g. `plans/john-doe/`, `reviews/john-doe/`) — see [docs/named-roadmaps.md](docs/features/named-roadmaps.md).

Consumer skills in the sibling `skills/` repository mirror this file protocol in their `orchestrator-artifacts` engine — any change to the protocol (directory layout, artifact naming, PASS signals, sidecar fields, review-section format) must be reflected there.

`_run_claude()` in `agents.py` shells out to the `claude` CLI with `--output-format stream-json` and parses `result`/`session_id`. Pass/fail is detected by `PLAN_REVIEW_PASS` (plan review) or `REVIEW_PASS` (code review) as the last line of the respective file.

## Target project requirements

What a target project needs (roadmap/task format, phases, the `---STOP---` breakpoint, `ARCHITECTURE`/`RULES` files, git) — [docs/target-project.md](docs/reference/target-project.md). The parsing itself lives in `roadmap.py`.

## Configuration

All settings live in `orchestrator.json` (project root, gitignored — copy from `orchestrator.json.example`; path override via `ORCHESTRATOR_CONFIG`). Every key, the agent models, and Telegram alerts — [docs/configuration.md](docs/reference/configuration.md). Defaults are set in `config.py` and when instantiating agents in `process_task()`.
