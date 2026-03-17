# Orchestrator

Generic AI agent orchestrator that autonomously plans, implements, and reviews tasks from a roadmap.

## How it works

Three agents work in a loop over each milestone in your `.ai-factory/ROADMAP.md`:

```
Agent 1 (orchestrator) — picks next unchecked milestone
  │
  ├── Agent 2 (planner) — analyzes codebase, writes plan to .ai-factory/plans/
  │
  ├── Agent 3 (implementer) — reads plan + patches, writes code
  │
  ├── Agent 2 (reviewer) — reviews changes against plan
  │     if issues → writes patch to .ai-factory/patches/
  │     Agent 3 re-implements (max 3 iterations)
  │
  ├── git commit
  └── mark milestone done in ROADMAP.md
```

Agents communicate through files, not shared context. Each agent starts fresh with only what it needs.

## Setup

```bash
cd orchestrator
uv sync
```

Requires `claude` CLI installed and authenticated (Claude Code).

## Usage

```bash
# Run on a project directory
uv run orchestrator /path/to/project

# Run on current directory
uv run orchestrator
```

The target project must have `.ai-factory/ROADMAP.md` with milestones in this format:

```markdown
- [ ] **Milestone title** — Description of what needs to be done
- [x] **Done milestone** — Already completed
```

## Project structure

```
orchestrator/
├── __init__.py
├── main.py          # Agent 1 — milestone loop, git commits
├── agents.py        # Agent 2/3 runners via Claude Code CLI
├── roadmap.py       # Parse/update ROADMAP.md checkboxes
└── prompts/
    ├── planner.md   # System prompt — create implementation plan
    ├── implementer.md  # System prompt — implement tasks from plan
    └── reviewer.md  # System prompt — review implementation
```

## File conventions

Plans and patches use sequential numbering:

```
.ai-factory/plans/01-milestone-slug.md
.ai-factory/plans/02-milestone-slug.md
.ai-factory/patches/01-milestone-slug-review-1.md
.ai-factory/patches/01-milestone-slug-review-2.md
```

## Prerequisites

- Python 3.11+
- [Claude Code](https://claude.ai/code) CLI installed and authenticated (`claude` in PATH)
- No API key needed — uses your Claude subscription

## Configuration

| Constant | File | Default | Description |
|---|---|---|---|
| `MAX_REVIEW_ITERATIONS` | `main.py` | 3 | Max review cycles per milestone |

### Agent model & effort defaults

| Agent | Model | Effort | Notes |
|---|---|---|---|
| Planner | `opus` | `high` | Same session as reviewer |
| Reviewer | `opus` | `medium` | Same session as planner, effort changes per call |
| Implementer | `sonnet` | `high` | Separate session |

Override in `main.py` when creating agents:
```python
planner = PlannerReviewer(project_dir, model="opus", plan_effort="high", review_effort="medium")
implementer = Implementer(project_dir, model="sonnet", effort="high")
```
