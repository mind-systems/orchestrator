# Plan: Per-milestone usage check + configurable phase sessions

## Context
Replace the adaptive `UsageGuard` with a simple per-milestone usage check that enforces two thresholds (session + weekly), and make phase-session carry-forward toggleable via env var for A/B token-cost comparison.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Core logic (`orchestrator/main.py`)

- [x] **Task 1: Replace usage-parsing helpers and guard with per-milestone check**
  Files: `orchestrator/main.py`
  Delete the `UsageGuard` class (lines ~39-74) and the `_parse_usage_pct()` function (lines ~29-36).
  Add a shared `_parse_pct(text: str, pattern: str) -> float | None` helper that runs `re.search(pattern, text)` and returns the first capture group as `float`, or `None` on no match.
  Add `_check_usage_limits() -> None` per the spec (`.ai-factory/notes/11-usage-guard-and-phase-session-config.md`, Task 1):
  - Run `subprocess.run(["claude", "/usage"], capture_output=True, text=True, timeout=30)` inside a try/except — on any exception, print a warning (e.g. `  [usage check: could not parse output, continuing]`) and return (never crash).
  - Parse session pct with `r"Current session:\s+(\d+(?:\.\d+)?)%"` and weekly pct with `r"Current week \(all models\):\s+(\d+(?:\.\d+)?)%"`.
  - Build a parts list and print `  [usage: session N% · week N%]` (only include parts that parsed).
  - Read `ORCHESTRATOR_USAGE_THRESHOLD` (default `90`) and `ORCHESTRATOR_WEEKLY_THRESHOLD` (default `95`) as floats.
  - Raise `PipelineStopError` if `session_pct >= session_threshold`, then (separately) if `weekly_pct >= weekly_threshold`, with the messages shown in the spec.
  Remove the now-unused `import math` (top of file) — verify `math` is referenced nowhere else first.

- [x] **Task 2: Wire the check + configurable phase sessions into both loops** (depends on Task 1)
  Files: `orchestrator/main.py`
  In `_implement_loop` and `_test_loop`:
  - Remove the `threshold = ...` / `guard = UsageGuard(...)` lines and the `guard.check(i)` call.
  - Before the section/phase-session handling in the per-milestone loop, call `_check_usage_limits()` (after the `state.stop_requested` check, so it runs before every milestone including the first).
  - Add `phase_sessions_enabled = os.environ.get("ORCHESTRATOR_PHASE_SESSIONS", "true").lower() != "false"` near where `current_section` / `phase_session_id` are initialized.
  - Replace the section-change reset with the spec's branching so the phase session also resets within the same section when disabled:
    ```python
    if milestone.section != current_section:
        current_section = milestone.section
        phase_session_id = None
    elif not phase_sessions_enabled:
        phase_session_id = None
    ```
  Remove the now-unused `before_each` parameter from `_run_loop` (the inline loops call `_check_usage_limits()` directly and `_run_loop` is the only consumer of `before_each`). Leave the rest of `_run_loop` intact.

### Phase 2: Documentation

- [x] **Task 3: Update `docs/configuration.md`** (depends on Task 2)
  Files: `docs/configuration.md`
  - Add a `ORCHESTRATOR_WEEKLY_THRESHOLD` row (default `95`) and a `ORCHESTRATOR_PHASE_SESSIONS` row (default `true`) to the env-var table.
  - Update the `ORCHESTRATOR_USAGE_THRESHOLD` description: it is now checked before every milestone (no adaptive prediction), and is the session threshold of two independent thresholds.
  - Replace the `### ORCHESTRATOR_USAGE_THRESHOLD` section body: remove the adaptive/prediction steps; describe the per-milestone check, the two thresholds (session + weekly all-models), the `[usage: session N% · week N%]` log line giving per-milestone delta visibility, and the fail-safe (parse failure → warn, continue).
  - Add a short `### ORCHESTRATOR_WEEKLY_THRESHOLD` description and a `### ORCHESTRATOR_PHASE_SESSIONS` description (when `false`, each milestone starts a fresh PlannerReviewer session regardless of section, for A/B token-cost comparison).
  - Add an inline example overriding both thresholds (e.g. `ORCHESTRATOR_USAGE_THRESHOLD=85 ORCHESTRATOR_WEEKLY_THRESHOLD=90 ...`).
  Keep all prose in Russian to match the existing file.

- [x] **Task 4: Update `docs/how-it-works.md`** (depends on Task 2)
  Files: `docs/how-it-works.md`
  - In `## Лимит использования сессии`: remove the "адаптивная"/rolling-delta/prediction paragraph; describe the check running before every milestone against two limits — сессионный (`ORCHESTRATOR_USAGE_THRESHOLD`, default 90) and недельный all-models (`ORCHESTRATOR_WEEKLY_THRESHOLD`, default 95) — either of which stops the run; mention the `[usage: session N% · week N%]` log line and the parse-failure fail-safe.
  - In `## Фазы роадмапа и сессии планировщика`: note that `ORCHESTRATOR_PHASE_SESSIONS=false` disables phase-session carry-forward, so every milestone starts a fresh session even within one phase.
  Keep all prose in Russian to match the existing file.
