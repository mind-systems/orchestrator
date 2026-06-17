# Plan: Config file — replace env vars with explicit config

## Context
Replace all five `os.environ.get("ORCHESTRATOR_*", default)` reads with a required `~/.orchestrator.json` config file, loaded once into an `OrchestratorConfig` dataclass at the top of `cli()` and threaded through every call site — no silent defaults anywhere.

## Settings
- Testing: no
- Logging: minimal
- Docs: yes

## Tasks

### Phase 1: Config module

- [x] **Task 1: Create `OrchestratorConfig` dataclass and `load_config()`**
  Files: `orchestrator/config.py`
  New module. Define a frozen-style `@dataclass OrchestratorConfig` with fields `max_iterations: int`, `usage_threshold_5h: float`, `usage_threshold_weekly: float`, `enable_phase_sessions: bool`. Implement `load_config() -> OrchestratorConfig`:
  - Resolve path from `os.environ.get("ORCHESTRATOR_CONFIG", "~/.orchestrator.json")` then `Path(...).expanduser()`. `ORCHESTRATOR_CONFIG` is the only env var allowed to remain in the codebase.
  - Missing file → `raise SystemExit(...)` with a message that includes the resolved path and an example JSON containing all four keys.
  - Invalid JSON → `raise SystemExit(...)` naming the path and the parse error (`json.JSONDecodeError`).
  - Iterate the four required keys; first missing key → `raise SystemExit(f"Missing required key '{key}' in {path}")`.
  - Construct the dataclass coercing types: `int(...)`, `float(...)`, `float(...)`, `bool(...)`. JSON key `usage_threshold_5h` maps to dataclass field `usage_threshold_5h`.
  Follow the reference implementation in `.ai-factory/notes/12-config-file.md`.

### Phase 2: Wire config through main.py

- [x] **Task 2: Load config in `cli()` and thread into entry points** (depends on Task 1)
  Files: `orchestrator/main.py`
  - Add `from .config import OrchestratorConfig, load_config`.
  - In `cli()`, remove `max_iterations = int(os.environ.get("ORCHESTRATOR_MAX_ITERATIONS", "3"))` (line ~749). Call `config = load_config()` right after resolving `project_dir`. Let `SystemExit` from `load_config()` propagate (it exits before the `try` that catches `PipelineStopError`/`RateLimitError`).
  - Change `run_test(project_dir, max_iterations)` / `run_implement(project_dir, max_iterations)` calls to pass `config` instead.
  - Update `run_implement` and `run_test` signatures from `max_iterations: int = 3` to `config: OrchestratorConfig`, and update their `_with_caffeinate(_implement_loop, project_dir, config)` / `_with_caffeinate(_test_loop, project_dir, config)` calls.

- [x] **Task 3: Replace phase-session and max-iteration env reads in the loops** (depends on Task 2)
  Files: `orchestrator/main.py`
  - `_implement_loop` and `_test_loop`: change signature to accept `config: OrchestratorConfig` (drop the `max_iterations: int = 3` param).
  - Replace both `phase_sessions_enabled = os.environ.get("ORCHESTRATOR_PHASE_SESSIONS", "true").lower() != "false"` reads (lines ~658, ~700) with `phase_sessions_enabled = config.enable_phase_sessions`.
  - Pass `config` into `process_milestone(...)` / `process_test_milestone(...)` and `_check_usage_limits(config)` calls inside the loops.

- [x] **Task 4: Thread config into `process_milestone` and `process_test_milestone`** (depends on Task 3)
  Files: `orchestrator/main.py`
  - Replace the `max_iterations: int = 3` parameter on both `process_milestone` and `process_test_milestone` with `config: OrchestratorConfig`. Keep other params (`planner_prompt_name`, `roadmap_filename`, `phase_session_id`).
  - Inside each function, derive `max_iterations = config.max_iterations` once near the top so the existing loop logic (`range(..., max_iterations + 1)`, guard checks) stays unchanged.
  - Update the two `PipelineStopError` messages that say "Bump ORCHESTRATOR_MAX_ITERATIONS to continue." to reference raising `max_iterations` in `~/.orchestrator.json` instead.

- [x] **Task 5: Thread config into `_check_usage_limits`** (depends on Task 4)
  Files: `orchestrator/main.py`
  - Change signature to `_check_usage_limits(config: OrchestratorConfig) -> None`.
  - Replace `session_threshold = float(os.environ.get("ORCHESTRATOR_USAGE_THRESHOLD", "90"))` with `session_threshold = config.usage_threshold_5h` and `weekly_threshold = float(os.environ.get("ORCHESTRATOR_WEEKLY_THRESHOLD", "95"))` with `weekly_threshold = config.usage_threshold_weekly` (lines ~57–58).
  - Confirm no `os.environ.get("ORCHESTRATOR_...")` calls remain except the `ORCHESTRATOR_CONFIG` read in `config.py`. Remove the now-unused `import os` from `main.py` only if nothing else uses it.

### Phase 3: Docs

- [x] **Task 6: Update all docs** (depends on Task 5)
  Files: `CLAUDE.md`, `docs/configuration.md`, `docs/how-it-works.md`, `README.md`, `.ai-factory/DESCRIPTION.md`
  - `CLAUDE.md`: add a config-file creation step to the Commands/Quick Start section (the `cat > ~/.orchestrator.json` heredoc with all four fields from the spec, marked as required before first run). Update the Key constants section: replace the `ORCHESTRATOR_MAX_ITERATIONS` env-var bullet with a description of the `~/.orchestrator.json` fields and the `ORCHESTRATOR_CONFIG` path override.
  - `docs/configuration.md`: this file is already written in the "Файл конфигурации" form. Verify it matches the final field names and behavior (`max_iterations`, `usage_threshold_5h`, `usage_threshold_weekly`, `enable_phase_sessions`, `ORCHESTRATOR_CONFIG` override, the `[usage: session N% · week N%]` log line, the PlannerReviewer phase-session note). Adjust only if anything drifted; do not reintroduce per-setting env vars.
  - `docs/how-it-works.md`: reword the four env-var references to use config field names — L7 and L9 (`ORCHESTRATOR_MAX_ITERATIONS` → `` `max_iterations` in `~/.orchestrator.json` ``), L35 (`ORCHESTRATOR_PHASE_SESSIONS=false` → `` `enable_phase_sessions: false` in config ``), L39 (`ORCHESTRATOR_USAGE_THRESHOLD`/`ORCHESTRATOR_WEEKLY_THRESHOLD` → `` `usage_threshold_5h` ``/`` `usage_threshold_weekly` ``).
  - `README.md`: L48 in the docs table — change "Env-переменные" to "Файл конфигурации".
  - `.ai-factory/DESCRIPTION.md`: L10 replace `configurable via \`ORCHESTRATOR_MAX_ITERATIONS\`` → `configurable via \`max_iterations\` in \`~/.orchestrator.json\``; L59 replace the `ORCHESTRATOR_MAX_ITERATIONS env var (default 3)` bullet with `\`max_iterations\` field in \`~/.orchestrator.json\` (default 3)`.

## Commit Plan
- **Commit 1** (after tasks 1-2): "Add config module and load config in CLI"
- **Commit 2** (after tasks 3-5): "Read all settings from config file instead of env vars"
- **Commit 3** (after task 6): "Document orchestrator config file"
