# Code Review: Fix stderr pipe deadlock in `_run_claude`

## Scope
`orchestrator/agents.py` — `_run_claude()`. New plan/plan-review files are non-code artifacts.

## Findings

None. The change matches the plan exactly and is correct:

- **Deadlock fixed**: `stderr=subprocess.STDOUT` merges stderr into the stdout pipe, which is already drained line-by-line via `for line in proc.stdout`. The subprocess can no longer block on a full 64 KB stderr pipe.
- **Stale read removed**: `proc.stderr.read()` after `proc.wait()` is deleted. With `STDOUT` merging, `proc.stderr` is `None`, so this read would have been useless and is the deadlock source the milestone targeted.
- **No dangling references**: Both `RuntimeError` messages no longer reference the removed `stderr` local. A full scan confirms no other use of that variable remains in the function. The only remaining `stderr` in the file is the unrelated Popen at line ~421, which already uses `subprocess.STDOUT`.
- **Robust to interleaving**: Non-JSON stderr lines now flow through the stdout loop, but `json.loads` is wrapped in `try/except json.JSONDecodeError` both in the read loop and the `parsed_final` search, so they are ignored gracefully.
- **Diagnostics preserved**: On non-zero exit, merged stderr content is still surfaced through `stdout` in the error message.

REVIEW_PASS
