# Orchestrator

Generic AI agent orchestrator that autonomously plans, implements, and reviews tasks from a roadmap.

## How it works

### Implement mode (default)

Three agents work in a loop over each milestone in your `.ai-factory/ROADMAP.md`:

```
Orchestrator — picks next unchecked milestone
  │
  ├── Planner — analyzes codebase, writes plan to .ai-factory/plans/
  │
  ├── Implementer — reads plan + patches, writes code
  │
  ├── Reviewer — reviews changes, writes findings to .ai-factory/reviews/
  │     if issues → Implementer fixes (max 3 iterations)
  │
  ├── git commit
  └── mark milestone done in ROADMAP.md
```

### Review mode

Audits all existing plans against the current codebase:

```
Orchestrator — iterates over all files in .ai-factory/plans/
  │
  ├── Reviewer — reviews code against plan, writes findings to .ai-factory/reviews/
  │     if issues:
  │       ├── Planner — creates detailed patch from review findings
  │       ├── Implementer — applies the patch
  │       └── Reviewer — re-reviews (max 3 iterations)
  │
  └── git commit
```

## Setup

```bash
cd orchestrator
uv sync
```

Requires `claude` CLI installed and authenticated (Claude Code).

## Usage

```bash
# Implement milestones from roadmap
uv run orchestrator implement /path/to/project

# Review all existing plans against current codebase
uv run orchestrator review /path/to/project

# Default (implement) on current directory
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
├── main.py          # Orchestrator loop, git commits, CLI
├── agents.py        # Planner/Reviewer/Implementer via Claude Code CLI
├── roadmap.py       # Parse/update ROADMAP.md checkboxes
└── prompts/
    ├── planner.md
    ├── implementer.md
    └── reviewer.md
```

## File conventions

```
.ai-factory/plans/01-milestone-slug.md
.ai-factory/reviews/01-milestone-slug-review-1.md
.ai-factory/patches/01-milestone-slug-patch-1.md
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
| Planner | `opus` | `high` | Fresh session each call |
| Reviewer | `opus` | `medium` | Fresh session, no shared context |
| Implementer | `sonnet` | `high` | Session persists across fix iterations |

Override when creating agents:
```python
planner = Planner(project_dir, model="opus", effort="high")
reviewer = Reviewer(project_dir, model="opus", effort="medium")
implementer = Implementer(project_dir, model="sonnet", effort="high")
```
