# Resume Guard + Write Hardening — Three Follow-Up Fixes

Found during code review of milestone 19 (sidecar robustness).

## Fix 1: Guard empty loop on resume after max_iterations

After milestone 19's Fix 2, when a pipeline stops at max_iterations the sidecar
records `step="review_failed:N"` (or `test_run_failed:N`). On the next run,
`_detect_milestone_step` returns `("implement", N+1)`. With default
`max_iterations=3`, `impl_start=4` → `range(4, 4)` is empty → the implement/review
loop body never executes → falls straight through to `mark_done()` + `_git_commit()`
— commits unfinished code as done without any warning.

Before milestone 19 the sidecar held `"implemented"`, so the resume restarted from
iteration 1 (buggy, but at least it ran). The new behavior is a silent data-loss
regression for anyone who re-runs without bumping `ORCHESTRATOR_MAX_ITERATIONS`.

Fix: add a guard at the start of both implement/review loops in `main.py`:

```python
# process_milestone() — before: for iteration in range(impl_start, max_iterations + 1):
if impl_start > max_iterations:
    raise PipelineStopError(
        f"Resume at iteration {impl_start} exceeds max_iterations "
        f"({max_iterations}). Bump ORCHESTRATOR_MAX_ITERATIONS to continue."
    )

# same guard in process_test_milestone()
```

Files: `orchestrator/main.py` — two insertion points.

## Fix 2: Guard `_write_session` internal read against corrupt sidecar

`_read_sessions` is now fault-tolerant (milestone 19, Fix 1), but `_write_session`
still does an unguarded `json.loads(p.read_text())` on its first line. A sidecar
left corrupt by a pre-milestone-19 crash survives the resume read (`_read_sessions`
returns `{}`) but crashes the next write with `JSONDecodeError`. Fix 1's resilience
guarantee is incomplete without this.

```python
def _write_session(plan_path: Path, key: str, value: str) -> None:
    p = plan_path.with_suffix('.json')
    try:
        data = json.loads(p.read_text()) if p.exists() else {}
    except (json.JSONDecodeError, OSError):
        data = {}
    data[key] = value
    tmp = p.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, p)
```

File: `orchestrator/agents.py` — `_write_session` only.

## Fix 3: Add `*.json.tmp` to `.gitignore`

`_write_session` (milestone 19, Fix 3) writes a sibling `*.json.tmp` file then
atomically replaces the target. A `kill -9` between those two operations leaves
the `.json.tmp` behind. `.gitignore` currently has no `*.tmp` rule, so a stale
`.json.tmp` would appear in `git status` and be picked up by `git add -A` in the
next `_git_commit()` call — committing an orphaned temp file.

Fix: add one line to `.gitignore`:

```
*.json.tmp
```

File: `.gitignore` — one line.

## Scope

- `orchestrator/main.py`: Fix 1 (two guard insertions)
- `orchestrator/agents.py`: Fix 2 (one try/except in `_write_session`)
- `.gitignore`: Fix 3 (one line)
