# Session ID Persistence in Plan Files

## Problem

`PlannerReviewer` and `Implementer` store their Claude session IDs in memory (`self.session_id`). When the orchestrator crashes or is interrupted, these are lost. On restart, `_detect_milestone_step()` correctly resumes from the right step, but both agents start fresh sessions — losing the planner's full context that the reviewer was supposed to inherit, and the implementer's working context mid-fix.

Concrete case: PlanReviewer ran 50 minutes, CLI exited code 1 (turns exhausted). On restart, the planner_reviewer and implementer were new sessions with no prior context.

## Solution

Store session IDs at the end of each plan file as an HTML comment block. The plan file is already the per-milestone source of truth. Agents read the plan file for context but ignore HTML comments. Session IDs won't be confused with spec content.

**Block format** (appended at the end of the plan file, after all plan content):

```
<!-- orchestrator-sessions
planner: 8fc29411-f9db-4379-8780-3e36eb547088
implementer: d72dc86d-0477-4da4-b6e1-4114923c1b19
-->
```

## Scope

- `process_milestone()` — implement flow: persist + restore `planner` and `implementer` sessions
- `process_test_milestone()` — test flow: same two roles
- **Not** refactor flow (`process_refactor_milestone`) — RefactorPlanner already tracks its own session in-memory and its sessions are shorter

## Implementation: agents.py

Add `import re` at the top.

Add two module-level helpers after the existing constants:

```python
_SESSIONS_RE = re.compile(r'<!-- orchestrator-sessions\n(.*?)\n-->', re.DOTALL)

def _read_sessions(plan_path: Path) -> dict[str, str]:
    if not plan_path.exists():
        return {}
    text = plan_path.read_text()
    m = _SESSIONS_RE.search(text)
    if not m:
        return {}
    result = {}
    for line in m.group(1).splitlines():
        if ': ' in line:
            k, v = line.split(': ', 1)
            result[k.strip()] = v.strip()
    return result

def _write_session(plan_path: Path, role: str, session_id: str) -> None:
    if not plan_path.exists() or not session_id:
        return
    text = plan_path.read_text()
    m = _SESSIONS_RE.search(text)
    if m:
        lines = m.group(1).splitlines()
        new_lines, found = [], False
        for line in lines:
            if line.startswith(f'{role}: '):
                new_lines.append(f'{role}: {session_id}')
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f'{role}: {session_id}')
        replacement = '<!-- orchestrator-sessions\n' + '\n'.join(new_lines) + '\n-->'
        text = text[:m.start()] + replacement + text[m.end():]
    else:
        text = text.rstrip('\n') + f'\n\n<!-- orchestrator-sessions\n{role}: {session_id}\n-->\n'
    plan_path.write_text(text)
```

Call `_write_session` after each `_run_claude` that updates a session:

- `PlannerReviewer.plan()` → `_write_session(plan_path, "planner", self.session_id)`
- `PlannerReviewer.review()` → `_write_session(plan_path, "planner", self.session_id)`
- `Implementer.implement()` → `_write_session(plan_path, "implementer", self.session_id)`

`plan_path` is already a parameter of all three methods.

## Implementation: main.py

Add `_read_sessions` to the import from `.agents`.

In `process_milestone()`, after the agents are created (lines ~165–167) and after `_detect_milestone_step()` returns the canonical `plan_path`, add:

```python
if plan_path.exists():
    sessions = _read_sessions(plan_path)
    planner_reviewer.session_id = sessions.get("planner")
    implementer.session_id = sessions.get("implementer")
```

Repeat identically in `process_test_milestone()` (which is created by the pending test-runner milestone).

## Edge Cases

- **plan_path doesn't exist yet** (step == "plan", counter == 1): `_read_sessions` returns `{}`, session_ids stay `None`. Correct.
- **Sessions block exists but session has expired**: `_run_claude` with `--resume` to a dead session will fail with exit code 1. This is an existing failure mode, not a regression — and the full stdout is now shown (per the fix already applied).
- **plan step restarts** (counter > 1, planner session was saved): planner resumes its own session for the plan revision. Correct.
