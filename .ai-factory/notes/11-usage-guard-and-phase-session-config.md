# Usage guard rewrite + configurable phase sessions

**Date:** 2026-06-17
**Source:** conversation context

## Key Findings

- Replace adaptive UsageGuard with a simple per-milestone check — every milestone, no prediction math
- Add weekly limit check alongside session limit — two independent thresholds, either triggers a stop
- Phase session persistence becomes opt-out via env var — enables A/B comparison of token cost

## Details

### Task 1 — Per-milestone usage check with dual thresholds

Replace the adaptive `UsageGuard` class (prediction math, rolling delta, `next_check_at`) with a
simple function called before every milestone:

```python
def _check_usage_limits() -> None:
    """Parse /usage and stop if either threshold is breached."""
    output = subprocess.run(["claude", "/usage"], capture_output=True, text=True, timeout=30).stdout
    
    session_pct = _parse_pct(output, r"Current session:\s+(\d+(?:\.\d+)?)%")
    weekly_pct  = _parse_pct(output, r"Current week \(all models\):\s+(\d+(?:\.\d+)?)%")
    
    parts = []
    if session_pct is not None:
        parts.append(f"session {session_pct:.0f}%")
    if weekly_pct is not None:
        parts.append(f"week {weekly_pct:.0f}%")
    if parts:
        print(f"  [usage: {' · '.join(parts)}]")
    
    session_threshold = float(os.environ.get("ORCHESTRATOR_USAGE_THRESHOLD", "90"))
    weekly_threshold  = float(os.environ.get("ORCHESTRATOR_WEEKLY_THRESHOLD", "95"))
    
    if session_pct is not None and session_pct >= session_threshold:
        raise PipelineStopError(
            f"Session usage at {session_pct:.0f}% — stopping (threshold: {session_threshold:.0f}%)."
        )
    if weekly_pct is not None and weekly_pct >= weekly_threshold:
        raise PipelineStopError(
            f"Weekly usage at {weekly_pct:.0f}% — stopping (threshold: {weekly_threshold:.0f}%)."
        )
```

`_parse_pct(text, pattern) -> float | None` — shared helper, returns None on no match.

Called at the TOP of the inline loop in `_implement_loop` and `_test_loop`, before every milestone
(including the first — gives baseline visibility). If `/usage` parse fails entirely — log warning,
continue (never crash).

Delete the entire `UsageGuard` class and `_parse_usage_pct()`. Delete the `before_each` hook from
`_run_loop` (no longer needed — the inline loop calls `_check_usage_limits()` directly).

Output line printed before each milestone:
```
  [usage: session 26% · week 52%]
```

This gives full run dynamics — you see the delta per milestone in the log.

Env vars:
- `ORCHESTRATOR_USAGE_THRESHOLD` — session limit stop threshold (default `90`)  
- `ORCHESTRATOR_WEEKLY_THRESHOLD` — weekly limit stop threshold (default `95`)

### Task 2 — Configurable phase session persistence

Add `ORCHESTRATOR_PHASE_SESSIONS` env var (default `true`). When `false`, phase session is never
carried — each milestone starts a fresh PlannerReviewer session regardless of section.

```python
phase_sessions_enabled = os.environ.get("ORCHESTRATOR_PHASE_SESSIONS", "true").lower() != "false"
```

In the inline loop:
```python
if milestone.section != current_section:
    current_section = milestone.section
    phase_session_id = None
elif not phase_sessions_enabled:
    phase_session_id = None  # reset even within same section
```

This lets you run the same phase twice — once with `ORCHESTRATOR_PHASE_SESSIONS=false`, once
without — and compare session/weekly % consumed per milestone from the log output.

### Task 3 — Update docs

In `docs/configuration.md`:
- Replace adaptive UsageGuard description with: "checked before every milestone, two thresholds"
- Add `ORCHESTRATOR_WEEKLY_THRESHOLD` row to env var table
- Add `ORCHESTRATOR_PHASE_SESSIONS` row to env var table
- Add inline example showing both thresholds overridden

In `docs/how-it-works.md`:
- Update "Лимит использования сессии" section: remove "адаптивная" / rolling delta description,
  replace with "перед каждым milestone — два лимита: сессионный и недельный"
- Update "Фазы роадмапа" section: mention `ORCHESTRATOR_PHASE_SESSIONS=false` disables carry-forward

### Files to touch

- `orchestrator/main.py`: delete `UsageGuard`, `_parse_usage_pct`; add `_parse_pct`, `_check_usage_limits`; update `_implement_loop` and `_test_loop` inline loops; remove `before_each` from `_run_loop` if present
- `orchestrator/agents.py`: no changes
- `docs/configuration.md`: update env var table + descriptions
- `docs/how-it-works.md`: update two sections
