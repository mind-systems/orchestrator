# Plan: Fix stderr pipe deadlock in `_run_claude`

## Context
Prevent a potential deadlock in `_run_claude` by merging the subprocess's stderr into the already line-consumed stdout stream, removing the post-`wait()` blocking read of `proc.stderr`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Merge stderr into stdout

- [x] **Task 1: Merge stderr into the stdout stream**
  Files: `orchestrator/agents.py`
  In the `subprocess.Popen` call inside the retry loop (around line 135-142), change `stderr=subprocess.PIPE` to `stderr=subprocess.STDOUT` so stderr is captured by the existing `for line in proc.stdout` loop. This mirrors the pattern already used in the other Popen call at line ~421.

- [x] **Task 2: Remove the post-wait stderr read** (depends on Task 1)
  Files: `orchestrator/agents.py`
  Delete the line `stderr = proc.stderr.read() if proc.stderr else ""` (around line 171). With stderr merged into stdout, `proc.stderr` is `None` and this read is both unnecessary and a deadlock source.

- [x] **Task 3: Drop the `stderr` variable from RuntimeError messages** (depends on Task 2)
  Files: `orchestrator/agents.py`
  Update the two `RuntimeError` constructions that reference the now-removed `stderr` variable:
  - The exit-code-failure error (around lines 206-210): remove the `f"stderr: {stderr if stderr else '(empty)'}\n"` line. The merged stderr is already present in `stdout` (the joined `lines`), which is still included in the message.
  - The empty-stdout error (around lines 212-216): remove the `f"stderr: {stderr[:1000] if stderr else '(empty)'}"` line; keep a clear message that stdout was empty.
  Ensure no remaining references to the `stderr` local variable exist in the function after these edits.
