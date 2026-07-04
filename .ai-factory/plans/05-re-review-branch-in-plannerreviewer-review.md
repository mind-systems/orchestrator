# Plan: Re-review branch in `PlannerReviewer.review()`

## Context
`PlannerReviewer.review()` reuses one persistent session but sends the same generic prompt on every pass, so the reviewer anchors on its own earlier verdict and re-asserts already-fixed findings — burning iterations on false failures. Mirror `plan()`'s re-plan branch so that subsequent passes force per-finding re-verification against the current file contents.

## Settings
- Testing: no
- Logging: minimal
- Docs: yes (existing `docs/non-convergence.md` gets a new failure-mode section, in Russian to match the file)

## Tasks

### Phase 1: Prompt-level re-review branch

- [x] **Task 1: Add `prev_review_path` re-review branch to `review()`**
  Files: `orchestrator/agents.py`
  In `PlannerReviewer.review()` (currently `agents.py:283`), add a new parameter `prev_review_path: Path | None = None` to the signature (place it after `review_path`, before or alongside the other keyword args). Branch on it, mirroring the shape of `plan()`'s `plan_review_path` branch (`agents.py:253-270`):
  - When `prev_review_path` is set, build a **re-review prompt** that:
    - States this is a re-review after fixes were applied and names the previous review file (`{prev_review_path}`).
    - Instructs NOT to trust session memory about file contents — the code has changed since the last pass.
    - For each finding in the previous review: re-read the cited file via Read, quote the current content of the cited lines, then give a verdict **Fixed / Not fixed** with the quote as evidence.
    - Then run the normal full review for new issues (`git diff HEAD` + `git status`, read changed files in full, write to `{review_path}`) — same instructions as the existing generic prompt.
    - Keep the REVIEW_PASS instruction unchanged (end file with `REVIEW_PASS` on its own line if no findings at all).
  - When `prev_review_path` is `None`, use the existing generic prompt verbatim.
  Do NOT change the session model: `system_prompt=self.system_prompt if not self.session_id else None`, the `_run_claude` call, `_write_session`, or the `_has_signal` / REVIEW_PASS detection at the end. `PlanReviewer` is untouched.

### Phase 2: Wire the call site

- [x] **Task 2: Pass iteration-1's review file from the call site** (depends on Task 1)
  Files: `orchestrator/main.py`
  At the `review()` call in `process_milestone` (`main.py:376`), compute the previous iteration's review path and pass it. For `iteration > 1`, build `prev = reviews_dir / f"{seq}-{milestone.slug}-review-{iteration - 1}.md"` and pass `prev_review_path=prev` **only if `prev.exists()`** (resume paths may skip iterations); otherwise pass `None`. For `iteration == 1`, pass `None`. Keep the surrounding `git add -A`, `review_path` construction, and pass/fail handling unchanged.

### Phase 3: Document the failure mode

- [x] **Task 3: Add the stale-verdict failure mode to non-convergence docs** (depends on Task 1)
  Files: `docs/non-convergence.md`
  Add a new section describing this failure mode: a persistent-session reviewer re-asserting stale verdicts (re-reporting an already-fixed finding as "carried over / unaddressed" because it anchors on its own earlier pass rather than re-reading the current file), and the re-review prompt as the countermeasure (naming the prior review and forcing per-finding Fixed/Not-fixed re-verification with quotes). Write in **Russian** to match the existing file. Describe current behavior only — no change history. Fit it alongside the existing two terminal-stop patterns; do not restructure the existing sections.
