# Explicit Step Tracking — JSON Sidecar + Replace Heuristic Resume Detection

## Problem

Two issues with the current resume mechanism:

1. **Heuristic step detection.** `_detect_milestone_step()` infers the current pipeline step from indirect signals: `git diff HEAD`, presence of plan-review files, presence of review files. Critical failure: when `implementer.implement()` is interrupted mid-run (rate limit, crash), the tree is left dirty with no review file. On resume, the function sees "dirty tree + no review files" → returns `("review", 1)` → review runs on incomplete code.

2. **Sessions block pollutes plan file.** The `<!-- orchestrator-sessions ... -->` HTML comment at the bottom of each plan file is read by agent sessions when they `Read` the plan. It's internal orchestrator state that the agent doesn't need and shouldn't be distracted by.

## Solution

### 1. JSON sidecar file

Replace the `<!-- orchestrator-sessions -->` block with a sidecar file named `{slug}.json` in the same `plans/` directory as the plan markdown. If the plan is `plans/01-scaffold.md`, the sidecar is `plans/01-scaffold.json`.

Update `_read_sessions` and `_write_session` in `agents.py`:

```python
def _read_sessions(plan_path: Path) -> dict:
    p = plan_path.with_suffix('.json')
    if not p.exists():
        return {}
    return json.loads(p.read_text())

def _write_session(plan_path: Path, key: str, value: str) -> None:
    p = plan_path.with_suffix('.json')
    data = json.loads(p.read_text()) if p.exists() else {}
    data[key] = value
    p.write_text(json.dumps(data, indent=2))
```

No backward compat — drop the `_SESSIONS_RE` regex and the old HTML comment logic entirely. Old plan files that still have the comment block simply have no sidecar; `_read_sessions` returns `{}` and they resume via heuristic fallback.

### 2. Explicit step tracking

Write the completed step to the sidecar after each phase in `process_milestone()` using `_write_session(plan_path, "step", value)`. On resume, `_detect_milestone_step()` reads `sessions.get("step")` first; if present, maps directly to `(step, counter)` — no git checks, no file globbing.

State transitions to write in `process_milestone()`:

| After | Write `step` value |
|---|---|
| `planner_reviewer.plan()` succeeds | `"planned"` |
| plan_review fails at attempt N | `"plan_review_failed:N"` |
| plan_review passes | `"plan_reviewed"` |
| `implementer.implement()` succeeds | `"implemented"` |
| review fails at iteration N | `"review_failed:N"` |

Resume mapping in `_detect_milestone_step()`:

| `step` value | Return |
|---|---|
| absent / empty | fall back to current heuristic (covers old plan files) |
| `"planned"` | `("plan_review", 1)` |
| `"plan_review_failed:N"` | `("plan", N+1)` |
| `"plan_reviewed"` | `("implement", 1)` |
| `"implemented"` | `("review", 1)` |
| `"review_failed:N"` | `("implement", N+1)` |

Key property: if `implement` is interrupted, `step` remains `"plan_reviewed"` → re-run implement. If `plan` is interrupted mid-session, `step` is either absent or from the previous attempt → re-run plan.

## Scope

- `agents.py`: replace `_SESSIONS_RE`, `_read_sessions`, `_write_session` with JSON sidecar versions; add `import json` if not present
- `process_milestone()` + `_detect_milestone_step()` in `main.py` — add `_write_session` calls after each phase; update detection logic to read `step` first
- `process_test_milestone()` + `_detect_test_milestone_step()` — same pattern; use `"test_run_failed:N"` instead of `"review_failed:N"`
- Refactor mode — skip; heuristic fallback in `_detect_milestone_step()` covers it unchanged
- Prompts, roadmap parsing, git commit logic — untouched
