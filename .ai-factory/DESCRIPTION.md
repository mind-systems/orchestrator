# Project: Orchestrator

## Overview

Orchestrator is an AI-driven development automation tool that processes milestones from a target project's roadmap and implements them autonomously using a multi-agent pipeline. It orchestrates Claude agents (Planner, Reviewer, Implementer) to plan, implement, and review code changes milestone by milestone, committing results to git after each completed milestone.

## Core Features

- Reads milestones from `.ai-factory/ROADMAP.md` in the target project
- Three-agent pipeline: plan → implement → review (with up to 3 review iterations)
- Session-persistent agents: PlannerReviewer runs as Opus with `--resume`; Implementer runs as Sonnet with `--resume`
- All agent communication through files (plans, patches), not shared memory
- Automatic git commit after each completed milestone
- CLI entry point: `uv run orchestrator [/path/to/project]`

## Tech Stack

- **Language:** Python 3.x
- **Package manager:** uv (pyproject.toml)
- **Runtime:** Shells out to `claude` CLI with `--output-format json`
- **No framework, no database** — pure Python CLI tool

## Architecture

### Agent Pipeline

```
main.py (Orchestrator loop)
  └── process_milestone()
        ├── PlannerReviewer (Opus, --resume) → .ai-factory/plans/<seq>-<slug>.md
        ├── Implementer (Sonnet, --resume)
        │     ← reads plan + patches
        └── PlannerReviewer (review pass, same session) → .ai-factory/patches/<seq>-<slug>-review-<n>.md
              └── detects REVIEW_PASS in output → commit or iterate
```

### Key Files

| File | Purpose |
|------|---------|
| `orchestrator/main.py` | Orchestrator loop, milestone driver, git commit |
| `orchestrator/agents.py` | PlannerReviewer and Implementer agent classes, `_run_claude()` |
| `orchestrator/roadmap.py` | ROADMAP.md parser — reads/writes `[ ]` / `[x]` milestones |
| `orchestrator/prompts/planner.md` | Combined planner+reviewer system prompt |
| `orchestrator/prompts/implementer.md` | Implementer system prompt |
| `orchestrator/prompts/reviewer.md` | Reviewer system prompt |

### Target Project Requirements

The project being orchestrated must have:
- `.ai-factory/ROADMAP.md` — milestones formatted as `- [ ] **Title** — Description`
- `.ai-factory/DESCRIPTION.md` — tech stack and conventions (read by planner)
- An initialized git repo

## Key Constants

- `MAX_REVIEW_ITERATIONS = 3` in `main.py`
- Default models: Planner=opus/high, Reviewer=opus/medium, Implementer=sonnet/high

## Non-Functional Requirements

- No test suite or linter configured
- Review pass/fail detected by the string `REVIEW_PASS` in reviewer output
- Session IDs tracked per agent to enable `--resume` continuity
