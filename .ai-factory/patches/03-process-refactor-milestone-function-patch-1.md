# Patch: process_refactor_milestone — bridge verify findings to patches_dir

## Issue

**Implementer is blind to verify findings on iteration 2+**

In `process_refactor_milestone`, when `RefactorPlanner.verify()` fails, the findings are written to `reviews_dir`. But the next call to `implementer.implement()` sends a continuation prompt (agents.py:308–310) telling the agent to read feedback from `patches_dir` — where nothing was written. The retry is effectively blind.

## Fix

**File:** `orchestrator/main.py`

**Location:** Inside the `else` branch at line 185, before the max-iteration check.

**Current code (lines 185–190):**
```python
        else:
            if iteration == max_refactor_iterations:
                raise PipelineStopError(
                    f"Max refactor iterations ({max_refactor_iterations}) reached.\n\n"
                    f"Last review: {review_path}\n\n{review_path.read_text()}"
                )
```

**Replace with:**
```python
        else:
            # Bridge verify findings to patches_dir so Implementer can read them
            patch_path = patches_dir / f"{seq}-{milestone.slug}-patch-{iteration}.md"
            patch_path.write_text(review_path.read_text())
            if iteration == max_refactor_iterations:
                raise PipelineStopError(
                    f"Max refactor iterations ({max_refactor_iterations}) reached.\n\n"
                    f"Last review: {review_path}\n\n{review_path.read_text()}"
                )
```

This copies the verify review into `patches_dir` as a patch file before either retrying or raising. On the next iteration, `Implementer.implement()` will find this file when it checks `patches_dir.glob("*.md")` and its continuation prompt will point the agent at real feedback.
