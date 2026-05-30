# Sidecar Robustness — Three Follow-Up Fixes

Found during code review of milestone 18 (JSON sidecar + explicit step tracking).

## Fix 1: Fault-tolerant `_read_sessions`

`json.loads` raises `JSONDecodeError` if the sidecar is empty or truncated (e.g. `kill -9` between file truncate and fsync). The old regex parser was fault-tolerant — no match → `{}`. This is a regression specifically for crash-resilience.

`orchestrator/agents.py`, `_read_sessions`:

```python
def _read_sessions(plan_path: Path) -> dict[str, str]:
    p = plan_path.with_suffix('.json')
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
```

## Fix 2: Write `step` before `PipelineStopError` at max iterations

In `process_milestone()` and `process_test_milestone()`, when the final iteration's review/test fails, `PipelineStopError` is raised **before** `_write_session(..., "step", f"review_failed:{iteration}")`. The sidecar retains `step="implemented"`. On the next run, `_detect_milestone_step` returns `("review", 1)` and **overwrites the failed review file** (`review-1.md`), losing the failure history.

Fix — move the `_write_session` call before the `max_iterations` check in both functions:

```python
# current (wrong order)
if iteration == max_iterations:
    raise PipelineStopError(...)
_write_session(plan_path, "step", f"review_failed:{iteration}")

# fixed
_write_session(plan_path, "step", f"review_failed:{iteration}")
if iteration == max_iterations:
    raise PipelineStopError(...)
```

Same fix needed for `test_run_failed` in `process_test_milestone()`.

## Fix 3: Atomic sidecar write via tmp + `os.replace`

`Path.write_text` truncates the file then writes. `kill -9` between those two operations leaves an empty or partial sidecar — the corruption that Fix 1 recovers from. Eliminate the window with an atomic replace:

```python
def _write_session(plan_path: Path, key: str, value: str) -> None:
    p = plan_path.with_suffix('.json')
    data = json.loads(p.read_text()) if p.exists() else {}
    data[key] = value
    tmp = p.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, p)
```

`os.replace` is atomic on POSIX — the file either has the old content or the new content, never a partial write.

## Scope

All three changes are in `orchestrator/agents.py` only. No changes to `main.py`, prompts, or roadmap parsing.
