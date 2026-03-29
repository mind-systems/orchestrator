# Review: process_refactor_milestone — patch fix

## Changes reviewed
- `orchestrator/main.py` lines 186–188 — two new lines bridging verify findings to `patches_dir`

## Analysis

The fix adds two lines inside the `else` branch (verify failed) of the implement-verify loop:

```python
patch_path = patches_dir / f"{seq}-{milestone.slug}-patch-{iteration}.md"
patch_path.write_text(review_path.read_text())
```

### Correctness

On iteration 2+, `Implementer.implement()` (agents.py:306–310) sends a continuation prompt referencing `patches_dir`. Before this fix, `patches_dir` had no relevant files. Now the verify review is copied there before the next iteration runs.

- `patches_dir` is created at line 153 (`mkdir(parents=True, exist_ok=True)`) — guaranteed to exist. Correct.
- `review_path` is written by `RefactorPlanner.verify()` before the `passed` check. If `verify` returns `False`, the review file exists (agents.py:379–381 checks `review_path.exists()` and returns `False` only if it doesn't). Correct.
- File naming (`{seq}-{milestone.slug}-patch-{iteration}.md`) is consistent with the pattern in `review_plan` (line 240). Correct.
- The copy happens before the max-iteration raise, so even on the last iteration the patch file is written (harmless — the error is raised immediately after). Correct.
- No imports needed — `Path.write_text` and `Path.read_text` are already used throughout the file. Correct.

### Edge cases

- `max_refactor_iterations=1`: Loop runs once. If verify fails, the `else` branch writes the patch (unused) then raises `PipelineStopError`. No harm — the patch file is inert.
- `patches_dir` contains old files from previous milestones: The Implementer's continuation prompt says "read the latest patch file" — the newly written file will have the current milestone's seq prefix, and `sorted(patches_dir.glob("*.md"))` puts it in order. The agent should pick it up correctly.

### No issues found

The fix is minimal, correct, and directly addresses the review-1 finding.

REVIEW_PASS
