# Re-review branch in `PlannerReviewer.review()` — stop anchoring on stale verdicts

**Date:** 2026-07-04
**Source:** conversation context (milestone-48 non-convergence diagnosis, tradeoxy_gui)

## Key Findings

- `PlannerReviewer.review()` (`agents.py:283-309`) sends the **same generic prompt on every pass** — unlike `plan()` (`agents.py:253-270`), which has an explicit re-plan branch that passes `plan_review_path` with "your plan was reviewed and has issues, read the review". `review()` has no such branch, yet its session is persistent across all passes of a milestone.
- Live incident (tradeoxy_gui milestone 48): the implementer applied both review findings on iteration 2 (verified in the working tree), but the reviewer's passes 2 and 3 claimed the code was "byte-identical to passes 1 & 2" and re-reported the already-fixed Finding 1 as "carried over, still unaddressed" — three iterations burned, pipeline stopped at max_iterations on a **false failure**. The persistent session anchors on its own earlier verdict instead of rereading the current file state.
- Fix: mirror `plan()`'s pattern. When `self.session_id` is already set (not the first review of this milestone), send a re-review prompt that names the previous review file and forces per-finding re-verification against the current file contents.

## Details

- **`agents.py` — `review()` signature:** add `prev_review_path: Path | None = None`. When set, use a re-review prompt instead of the generic one:
  - This is a re-review after fixes were applied. The previous review is at `{prev_review_path}`.
  - Do NOT trust session memory about the file contents — the code has changed since the last pass.
  - For each finding in the previous review: re-read the relevant file via Read, quote the current content of the cited lines, then verdict **Fixed / Not fixed** with the quote as evidence.
  - Then run the normal full review for new issues (`git diff HEAD`, read changed files in full — same as the generic prompt).
  - Write to `{review_path}`; REVIEW_PASS rules unchanged.
- **`main.py` — call site (`process_milestone`, ~line 376):** for `iteration > 1`, pass the previous iteration's review file: `reviews_dir / f"{seq}-{slug}-review-{iteration - 1}.md"` (pass only if it exists — resume paths may skip iterations). First iteration passes `None`.
- **Session model stays as-is:** the persistent planner-reviewer session is by design (reviewer keeps planner context). The fix is prompt-level, not session-level.
- **Docs:** add this failure mode (persistent-session reviewer re-asserting stale verdicts; the re-review prompt as the countermeasure) to `docs/non-convergence.md` — it currently describes the two terminal-stop patterns but not this false-failure cause. Describe current behavior only, no change history.
- **Verify:** run a milestone that fails review once; the iteration-2 review file must contain per-finding Fixed/Not-fixed verdicts with quotes.

## What NOT to do

- Do not make the reviewer session fresh per pass — losing planner context is the trade-off the architecture explicitly rejects (`agents.py:235` docstring).
- Do not change `_has_signal` / REVIEW_PASS detection.
- Do not touch `PlanReviewer` — it is already fresh-session per attempt and has no anchoring problem.
