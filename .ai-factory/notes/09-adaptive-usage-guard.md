# Adaptive Session Usage Guard

**Date:** 2026-06-17
**Source:** conversation context

## Key Findings

- `claude /usage` stdout contains `"Current session: N% used"` — parseable via regex
- The 5-hour session limit is what matters; weekly limits are not checked
- Adaptive algorithm minimizes checks: start → +1 → predict next check from rolling delta
- `ORCHESTRATOR_USAGE_THRESHOLD` env var (default `90`) controls the stop threshold
- `_run_loop` gets an optional `before_each(i, item)` hook (default `None`) — backward-compatible

## Details

### Parsing usage

```python
def _parse_usage_pct() -> float | None:
    result = subprocess.run(["claude", "/usage"], capture_output=True, text=True, timeout=30)
    m = re.search(r"Current session:\s+(\d+(?:\.\d+)?)%\s+used", result.stdout)
    return float(m.group(1)) if m else None
```

If the CLI returns no parseable output (e.g. offline, format change) — log a warning and continue; do not crash.

### UsageGuard class (in `main.py`)

```python
class UsageGuard:
    def __init__(self, threshold: float = 90.0):
        self.threshold = threshold
        self._history: list[tuple[int, float]] = []  # (milestone_idx, pct)
        self._next_check_at: int = 0

    def check(self, idx: int) -> None:
        if idx < self._next_check_at:
            return
        pct = _parse_usage_pct()
        if pct is None:
            print("  [usage check: could not parse output, continuing]")
            self._next_check_at = idx + 5
            return
        print(f"  [usage: session {pct:.0f}% used]")
        if pct >= self.threshold:
            raise PipelineStopError(
                f"Session usage at {pct:.0f}% — stopping (threshold: {self.threshold:.0f}%)."
            )
        self._history.append((idx, pct))
        self._next_check_at = self._predict_next(idx, pct)

    def _predict_next(self, idx: int, pct: float) -> int:
        if len(self._history) < 2:
            return idx + 1  # need one more data point to compute delta
        oldest_idx, oldest_pct = self._history[0]
        span = idx - oldest_idx
        if span == 0:
            return idx + 5
        avg_delta = (pct - oldest_pct) / span
        if avg_delta <= 0:
            return idx + 5  # usage not growing — check again in 5
        milestones_left = math.ceil((self.threshold - pct) / avg_delta)
        # Check one milestone before the predicted limit
        return idx + max(1, milestones_left - 1)
```

### Wiring into loops

`_run_loop` gains an optional `before_each` parameter:

```python
def _run_loop(items, process_fn, before_each=None) -> None:
    for i, item in enumerate(items):
        if _state.stop_requested:
            print(">>> Stop requested — halting.")
            return
        if before_each:
            before_each(i, item)
        process_fn(item)
```

Both `_implement_loop` and `_test_loop` create a `UsageGuard` and pass it:

```python
threshold = float(os.environ.get("ORCHESTRATOR_USAGE_THRESHOLD", "90"))
guard = UsageGuard(threshold=threshold)
_run_loop(
    enumerate(pending, start=_next_number(plans_dir)),
    lambda item: process_milestone(...),
    before_each=lambda i, item: guard.check(i),
)
```

### Typical check cadence

- Milestone 0: check → e.g. 20% → next_check_at = 1
- Milestone 1: check → e.g. 23% → delta = 3%/milestone → 90-23 = 67% left → 67/3 = 22 milestones → next_check_at = 1 + 21 = 22
- Milestone 22: check → e.g. 87% → delta refined → next_check_at = 23
- Milestone 23: check → 90% → PipelineStopError

Total: 4 checks for a 23-milestone run, instead of 23.

### Files to touch

- `orchestrator/main.py`: add `_parse_usage_pct()`, `UsageGuard`, extend `_run_loop` signature, wire into `_implement_loop` and `_test_loop`; add `import math` if not already present

## Open Questions

- `claude /usage` spawns a full Claude Code session — measure actual latency; if >5s, add a note to the log.
- If usage resets mid-run (clock crosses the 5-hour window), pct drops and delta goes negative — `avg_delta <= 0` branch handles this by scheduling a check in 5 milestones. Acceptable.
