# Implementer continuing-prompt points at the dead `patches/` dir in implement mode

**Date:** 2026-07-04
**Source:** conversation context (milestone-48 non-convergence diagnosis)

## Key Findings

- `Implementer.implement()` (`agents.py:368-390`): on continuing iterations (session already open) the prompt says "Review feedback has been written to `{patches_dir}`. Read the latest patch file there and apply the fixes."
- In **implement mode**, `patches_dir` is never populated: review feedback is written to `reviews_dir` (`main.py:375`), and nothing bridges it to `patches/`. The only writer of `patches/` is **test mode** (`main.py:637-639`, bridging TestRunner output). So in implement mode the implementer is pointed at an empty directory every fix iteration.
- In the milestone-48 run the implementer found `.ai-factory/reviews/` anyway by its own initiative (it has Bash/Grep) — the pipeline worked by luck of agent curiosity, not by contract. The fix makes the feedback location explicit.

## Details

- **`agents.py` — `implement()` signature:** replace the `patches_dir` param with an explicit feedback path. Add `feedback_path: Path | None = None`; when `self.session_id` is set, the prompt becomes: "Review feedback has been written to `{feedback_path}`. Read it and apply the fixes." (exact file, not a directory — no "latest file" guessing).
- **`main.py` implement mode (~line 369):** on iterations after a failed review, pass the failed review file: `reviews_dir / f"{seq}-{slug}-review-{iteration - 1}.md"`.
- **`main.py` test mode (~line 622):** pass the original TestRunner output file directly: `test_runs_dir / f"{seq}-{slug}-test-run-{iteration - 1}.md"` (exact name per the existing `test_run_path` construction). **Delete the bridge** (`main.py:637-639`) that copied this file into `patches/` — it existed only to conform to the old "feedback lives in patches/" convention, which this task retires.
- **Retire `patches/` entirely:** with the bridge gone, nothing writes to `patches/`. Remove its creation from both modes' directory setup (`main.py:257,261` and `main.py:514,517`) and drop the first-call `patches_note` scan in `implement()` (`agents.py:376-380`) — for resume, the caller passes the same explicit `feedback_path` when the previous iteration produced feedback, instead of the implementer scanning a directory. Resume behavior for both modes must not regress: an interrupted run resuming at an implement step after failed feedback must still receive the pointer.
- **Docs sweep:** `CLAUDE.md` (output-directories list), `docs/test-mode.md` ("вывод тестов попадает в patches/"), `docs/how-it-works.md` — describe the current state: feedback is passed as an explicit file path (review file in implement mode, test-run file in test mode); `patches/` no longer exists. Existing `patches/` directories in target projects are not deleted — writes retire, leftovers die naturally.
- **Verify:** in an implement-mode run with a failed first review, the iteration-2 implementer transcript must show it reading the named review file directly (no directory exploration); in a test-mode run with a failed test, iteration 2 must read the named test-run file; grep confirms no `patches` literal remains in `agents.py`/`main.py`.

## What NOT to do

- Do not have the reviewer start writing into `patches/` or anywhere new — reviews stay in `reviews/`, test runs in `test-runs/`; the fix is the pointer, not the file layout.
- Do not delete `patches/` directories in target projects — stop creating and writing, let leftovers rot.
