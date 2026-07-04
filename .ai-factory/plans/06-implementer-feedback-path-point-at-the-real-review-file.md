# Plan: Implementer feedback path — point at the real review file

## Context
Replace the dead `{patches_dir}` pointer in the Implementer's fix-iteration prompt with an explicit `feedback_path` (the failed review file in implement mode, the failed test-run file in test mode), and retire the `patches/` directory entirely across code, prompt, and docs.

## Settings
- Testing: no
- Logging: minimal
- Docs: yes (docs sweep is part of the milestone)

## Tasks

### Phase 1: Code — the pointer

- [x] **Task 1: Rework `Implementer.implement()` to take an explicit `feedback_path`**
  Files: `orchestrator/agents.py`
  Change the signature (line 384): drop the `patches_dir: Path` positional param and add `feedback_path: Path | None = None` (keep `plan_path`, `roadmap_path`, `line_number`). In the continuing branch (`if self.session_id:`, lines 386-390) set the prompt to: `f"Review feedback has been written to {feedback_path}. Read it and apply the fixes."` — an exact file, no "latest patch file" / directory-guessing wording. In the first-call `else` branch, delete the `patches_note` scan block (lines 392-396) that globs `patches_dir` entirely; the first-call prompt keeps only `roadmap_line` + `f"Implement the plan at: {plan_path}"`. Leave the `_run_claude(...)` call and `_write_session(...)` untouched.
  Also remove the two remaining `patches` mentions in this file so Task 3's grep gate is achievable: the class docstring (line 369, `"""Implements the plan, then applies fixes from patches. Same session."""`) → reword to drop "patches", e.g. `"""Implements the plan, then applies the review feedback for the current iteration. Same session."""`; and the inline comment on line 386 (`# Continuing — apply fixes from patches`) → reword to drop "patches", e.g. `# Continuing — apply the review feedback`.

- [x] **Task 2: Implement mode — pass the failed review file, stop creating `patches/`** (depends on Task 1)
  Files: `orchestrator/main.py`
  In `process_milestone()`: remove the `patches_dir` local (line 257) and its `mkdir` (line 261). At the implement call inside the loop (line 369), compute the feedback path just before the call: for `iteration > 1`, `feedback_path = reviews_dir / f"{seq}-{milestone.slug}-review-{iteration - 1}.md"`; for `iteration == 1`, `feedback_path = None`. Pass it: `implementer.implement(plan_path, feedback_path=feedback_path, roadmap_path=roadmap_path, line_number=milestone.line_number)`. This must hold on resume: when the loop starts at `impl_start = counter` after a failed review, the same `iteration - 1` review file is passed — verify the resume path (`step in ("implement", "review")`) still produces the correct pointer.

- [x] **Task 3: Test mode — pass the failed test-run file, delete the bridge, stop creating `patches/`** (depends on Task 1)
  Files: `orchestrator/main.py`
  In `process_test_milestone()`: remove `patches_dir` (line 519) and drop it from the `mkdir` loop tuple (line 522). At the implement call inside the loop (line 627), compute for `iteration > 1`: `feedback_path = test_runs_dir / f"{seq}-{milestone.slug}-test-{iteration - 1}.txt"` (match the exact `test_run_path` naming at line 633 — `-test-{n}.txt`, NOT the `-test-run-{n}.md` form written loosely in the spec); for `iteration == 1`, `None`. Pass `feedback_path=feedback_path` to `implementer.implement(...)`. Delete the copy-bridge in the failure branch (lines 642-644: the `patch_path = patches_dir / ...` + `patch_path.write_text(...)` lines). Confirm resume (`step in ("implement", "test_run")`) still yields the right pointer. After this task, `git grep -n patches -- 'orchestrator/*.py'` must return nothing.

### Phase 2: Prompt & docs sweep

- [x] **Task 4: Retire `patches/` from the implementer system prompt** (depends on Task 1)
  Files: `orchestrator/prompts/implementer.md`
  Line 5: change "You will be given the plan file path and the patches directory path." to state the implementer is given the plan file path, and on fix iterations an explicit review-feedback file path to read and apply. Step 0 (lines 22-26): delete the "Read all patches from `.ai-factory/patches/`" block (the `Glob` scan of `.ai-factory/patches/`) — the feedback file now arrives in the fix-iteration prompt as an exact path. Line 32: drop the "Avoid pitfalls documented in patches" bullet (or reword to "apply the review feedback for this iteration"). Do not introduce any new directory; the fix is the pointer, not a new file layout.

- [x] **Task 5: Docs sweep — describe the explicit-file feedback, drop `patches/`** (depends on Tasks 2, 3)
  Files: `CLAUDE.md`, `docs/how-it-works.md`, `docs/test-mode.md`
  `CLAUDE.md` line 68: remove `patches/` from the output-directories list (leave `plans/`, `plan-reviews/`, `reviews/`, `test-runs/`). `docs/how-it-works.md`: line 9 ("пишется патч, Implementer его применяет") and line 45 ("Implementer читает патч") — reword to say the reviewer's review file in `reviews/` is passed to the Implementer as an explicit path. `docs/test-mode.md` line 19 ("вывод тестов попадает в `patches/` и Implementer читает его … как обычный патч") — reword to say the test-run file in `test-runs/` is passed directly to the Implementer as the feedback path. Describe current state only; do not mention that `patches/` was removed. Note in no doc that target-project leftover `patches/` dirs are cleaned — they are not.
  **`docs/how-it-works.md` and `docs/test-mode.md` are written in Russian** — the reworded sentences MUST stay in Russian to match the surrounding prose; the English phrasings above are intent, not literal copy. `CLAUDE.md` is English.

- [x] **Task 6: Note the downstream consumer-skill obligation** (depends on Tasks 2, 3)
  Files: none in this repo — documentation-only callout in the plan.
  The project `CLAUDE.md` requires that the `orchestrator-artifacts` engine in `~/projects/skills` mirror any file-protocol change. Retiring `patches/` is a directory-layout change to that protocol, so consumer skills that read `patches/` (e.g. `milestone-rescue`) must be updated separately. That cross-repo edit is out of scope for this milestone, but flag it explicitly in the implementer's review handoff / commit body so the obligation is not silently dropped. Do not edit the skills repo here.

## Commit Plan
- **Commit 1** (after tasks 1-3): "Point implementer at explicit feedback file and retire patches directory"
- **Commit 2** (after tasks 4-6): "Sweep patches references from implementer prompt and docs" — mention the pending `~/projects/skills` consumer update in the commit body.
