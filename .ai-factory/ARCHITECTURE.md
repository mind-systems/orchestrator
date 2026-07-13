# Architecture: Layered Architecture

## Overview

The orchestrator is a small Python CLI tool with no framework, no database, and no complex domain logic. Layered Architecture fits the scale: one developer, ~10 small single-concern modules, a linear data flow from CLI to filesystem.

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
│   ├── main.py          # Orchestration: CLI, the unified milestone pipeline, roadmap loops, git commit
│   ├── agents.py        # Agents: agent classes, _run_claude(), sidecar session helpers, claude-CLI resolution
│   ├── roadmap.py       # Infrastructure: ROADMAP.md parsing, mark_done()/mark_skipped()
│   ├── config.py        # Support: config load + validation (global base + per-project overlay)
│   ├── usage.py         # Support: usage-threshold gating (/usage parse, session/weekly limits)
│   ├── resume.py        # Support: sidecar step detection / resume dispatch
│   ├── runtime.py       # Support: run + signal + process lifecycle (Ctrl+C, caffeinate, elapsed)
│   ├── notify.py        # Support: Telegram alerts
│   ├── state.py         # Shared mutable process state for one run
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

Direction: `main.py` → agents / support modules → `roadmap.py`, `state.py`

- ✅ `main.py` imports from `agents.py`, `roadmap.py`, and the support modules (`config`, `usage`, `resume`, `runtime`, `notify`)
- ✅ `agents.py` imports from `roadmap.py` (`_read_sessions`, `_write_session` only)
- ✅ support modules import downward only — `usage`→`config`; `resume`→`agents` (`_read_sessions`); `runtime`→`state`, `notify`, `agents` (`kill_active_child`); none import `main.py`
- ❌ `roadmap.py` must NOT import from `agents.py` or `main.py`
- ❌ `agents.py` must NOT import from `main.py`
- ✅ `state.py` may be imported from any layer (shared run state)

## Layer Responsibilities

**Orchestration (`main.py`)** — reads the roadmap, runs agents in the correct order, manages iterations, makes git commits. Knows the step sequence, not agent internals.

**Agents (`agents.py`)** — wrappers over the `claude` CLI. Each class encapsulates one agent type, manages `session_id`, reads/writes the JSON sidecar. Has no knowledge of roadmap structure or milestones.

**Infrastructure (`roadmap.py`)** — pure file operations: parsing markdown checkboxes, writing `[x]`, elapsed time. No dependencies on agents.

**Support modules** — single-concern helpers `main.py` composes, each depending only downward: `config.py` (load + validate settings, including the per-project overlay), `usage.py` (usage-threshold gating), `resume.py` (detect where a prior run stopped), `runtime.py` (run/signal/process lifecycle), `notify.py` (Telegram alerts), `state.py` (shared mutable state for one run).

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
| **Pipeline control** | |
| Iterative plan review gate | 15f1e77 |
| Crash recovery — mid-milestone resume | 48e435d |
| Test mode — real test runner gate | fb219a4 |
| Dynamic roadmap re-scan loop | a9b1c12 |
| Roadmap breakpoint marker | 9a4aa63 |
| **Session & observability** | |
| Phase-persistent planner session | 025658d |
| Per-milestone usage guard | b214041 |
| Telegram alerts (stop / milestone / done) | a3ceb9b |
| **Configuration** | |
| Project-root config file | 992a38e |
| **Internal** | |
| Roadmap drop history | 282007d |
