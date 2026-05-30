# Architecture: Layered Architecture

## Overview

The orchestrator is a small Python CLI tool with no framework, no database, and no complex domain logic. Layered Architecture fits the scale: one developer, ~5 source files, a linear data flow from CLI to filesystem.

Three layers separated by responsibility: orchestration, agents, infrastructure. Each layer knows only about the layers below it.

## Decision Rationale

- **Team size:** 1 developer → Layered
- **Domain complexity:** low (coordination of calls, no business rules) → Layered
- **Scale:** single process, local machine → Layered
- **Codebase size:** ~5 modules → Layered (Structured Modules fits at ~10+ modules)

## Folder Structure

```
orchestrator/
├── orchestrator/
│   ├── main.py          # Orchestration layer: CLI, process_milestone(), roadmap loop
│   ├── agents.py        # Agent layer: agent classes, _run_claude(), sidecar helpers
│   ├── roadmap.py       # Infrastructure layer: ROADMAP.md parsing, mark_done()
│   ├── state.py         # Global flag: stop_requested (Ctrl+C)
│   └── prompts/         # Static system prompts (data, not code)
│       ├── planner.md
│       ├── reviewer.md
│       ├── implementer.md
│       └── test-planner.md
├── .ai-factory/         # AI context (not source code)
├── docs/
├── pyproject.toml
└── CLAUDE.md
```

## Dependency Rules

Direction: `main.py → agents.py → roadmap.py`

- ✅ `main.py` imports from `agents.py` and `roadmap.py`
- ✅ `agents.py` imports from `roadmap.py` (`_read_sessions`, `_write_session` only)
- ❌ `roadmap.py` must NOT import from `agents.py` or `main.py`
- ❌ `agents.py` must NOT import from `main.py`
- ✅ `state.py` may be imported from any layer (global flag)

## Layer Responsibilities

**Orchestration (`main.py`)** — reads the roadmap, runs agents in the correct order, manages iterations, makes git commits. Knows the step sequence, not agent internals.

**Agents (`agents.py`)** — wrappers over the `claude` CLI. Each class encapsulates one agent type, manages `session_id`, reads/writes the JSON sidecar. Has no knowledge of roadmap structure or milestones.

**Infrastructure (`roadmap.py`)** — pure file operations: parsing markdown checkboxes, writing `[x]`, elapsed time. No dependencies on agents.

## Key Principles

1. **Agents communicate through files only** — no in-memory data passing between agents
2. **Sidecar is isolated** — `_read_sessions`/`_write_session` live in `agents.py` only
3. **Signals via last line of file** — `PLAN_REVIEW_PASS`, `REVIEW_PASS` — not via agent return values
4. **One class per agent type** — `PlannerReviewer`, `PlanReviewer`, `Implementer`, `TestRunner` are never mixed

## Code Examples

### Correct dependency direction

```python
# main.py — orchestration (top layer)
from .agents import PlannerReviewer, Implementer  # ✅ import down
from .roadmap import parse_roadmap, mark_done      # ✅ import down

# agents.py — agents (middle layer)
from .roadmap import _read_sessions, _write_session  # ✅ import down

# roadmap.py — infrastructure (bottom layer)
# no imports from agents or main ✅
```

### Adding a new agent

```python
# agents.py
class NewAgent:
    def __init__(self, project_dir: Path, model: str = "sonnet", effort: str = "high"):
        self.project_dir = project_dir
        self.system_prompt = _load_prompt("new-agent")
        self.session_id: str | None = None

    def run(self, plan_path: Path, output_path: Path) -> bool:
        _, self.session_id = _run_claude(
            prompt="...",
            cwd=str(self.project_dir),
            system_prompt=self.system_prompt if not self.session_id else None,
            session_id=self.session_id,
        )
        _write_session(plan_path, "new-agent", self.session_id)
        return output_path.read_text().strip().endswith("PASS")
```

## Anti-Patterns

- ❌ Passing data between agents via Python variables — files only
- ❌ Importing `main.py` from `agents.py` or `roadmap.py`
- ❌ Step-selection logic in `agents.py` — it belongs in `main.py`
- ❌ Calling the `claude` CLI directly from `main.py` — only via agent classes in `agents.py`
- ❌ Reading/writing `ROADMAP.md` from `agents.py` — only from `main.py` via `roadmap.py`

## Evolution Triggers

Move to **Structured Modules** when:
- `agents.py` grows beyond 700+ lines with unrelated classes
- 3+ independent domains emerge (e.g. orchestration, monitoring, reporting)
- Different parts need isolated testing with independent dependencies

## Feature History

| Feature | Commit |
|---------|--------|
| _(populated by `/roadmap-prune`)_ | — |
