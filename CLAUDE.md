# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
cd orchestrator && uv sync

# Run on a target project
uv run orchestrator /path/to/project

# Run on current directory
uv run orchestrator
```

No test suite or linter is configured.

## Architecture

Three-agent pipeline that processes milestones from a target project's `.ai-factory/ROADMAP.md`:

1. **PlannerReviewer** (`agents.py`) — runs as Opus with `--resume` to maintain session state across plan + review calls. First call uses the combined planner+reviewer system prompt; subsequent calls resume the same session.
2. **Implementer** (`agents.py`) — runs as Sonnet, also session-persistent across implement → fix-patch iterations.
3. **Orchestrator loop** (`main.py`) — drives the pipeline: plan → [implement → review] × up to `MAX_REVIEW_ITERATIONS` → mark done → git commit.

All agents communicate through files, not shared memory. The planner writes to `.ai-factory/plans/<seq>-<slug>.md`; the reviewer writes feedback patches to `.ai-factory/patches/<seq>-<slug>-review-<n>.md`; the implementer reads both.

`_run_claude()` in `agents.py` shells out to the `claude` CLI with `--output-format json` and parses `result`/`session_id` from the response. Review pass/fail is detected by the string `REVIEW_PASS` in the reviewer's output.

## Target project requirements

The project being orchestrated must have:
- `.ai-factory/ROADMAP.md` with milestones formatted as:
  ```
  - [ ] **Title** — Description
  ```
- `.ai-factory/DESCRIPTION.md` — tech stack and conventions (read by the planner agent)
- An initialized git repo (the orchestrator commits after each milestone)

## Key constants

- `MAX_REVIEW_ITERATIONS = 3` in `main.py`
- Default models/effort: Planner=opus/high, Reviewer=opus/medium, Implementer=sonnet/high — override when instantiating agents in `process_milestone()`
