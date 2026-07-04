# Code Review: Re-review branch in `PlannerReviewer.review()`

**Files reviewed:** `orchestrator/agents.py`, `orchestrator/main.py`, `docs/non-convergence.md` (full), against the plan and spec `.ai-factory/specs/01-reviewer-rereview-branch.md`.

## Verification against plan / spec

**Task 1 — `agents.py` `review()` re-review branch**
- Signature now `review(self, plan_path, review_path, prev_review_path: Path | None = None)` — new param last, backward-compatible. ✓
- Branches on `if prev_review_path:`, mirroring `plan()`'s `if plan_review_path:` shape. This correctly sidesteps the spec's literal "when `self.session_id` is already set" trigger, which would misfire on iteration 1 (the session already exists from `plan()`). The plan flagged this; the code follows the plan. ✓
- Re-review prompt: names the previous review file, instructs NOT to trust session memory, forces per-finding re-read via Read + current-line quote + Fixed/Not-fixed verdict, then runs the normal full review (`git diff HEAD` + `git status`, read files in full), and keeps the REVIEW_PASS-on-its-own-line rule. ✓
- Else-branch prompt is byte-for-byte the original generic prompt. ✓
- Session model untouched: `system_prompt=self.system_prompt if not self.session_id else None`, `_run_claude`, `_write_session`, and the `_has_signal(..., "REVIEW_PASS")` detection are all unchanged. `PlanReviewer` untouched. ✓

**Task 2 — `main.py` call site**
- For `iteration > 1`, computes `prev = reviews_dir / f"{seq}-{milestone.slug}-review-{iteration - 1}.md"` and passes it only when `prev.exists()`; iteration 1 (and a missing prior file on resume) passes `None`. ✓
- Filename scheme matches `review_path`'s own `-review-{iteration}.md`. Only caller of `review()` in the codebase. Surrounding `git add -A`, `review_path` construction, and pass/fail handling unchanged. ✓
- Resume path (`step == "review"`, `iteration == counter`): resuming mid-review at iteration N still finds `review-{N-1}.md` and correctly engages the re-review branch; the `exists()` guard handles skipped-iteration resumes gracefully. ✓

**Task 3 — `docs/non-convergence.md`**
- New `## Паттерн 3: устаревший вердикт персистентной сессии` section, in Russian, matching the file's style. Describes the stale-verdict anchoring, distinguishes it from Паттерн 2 (finding closed in code vs. unresolved semantics), and describes the re-review prompt countermeasure. Current-state only, no change history; existing sections not restructured. ✓

## Runtime / correctness
- No type mismatches: `prev_review_path` is `Path | None`; `if prev_review_path:` is safe for both.
- No signal/protocol change — `REVIEW_PASS` detection contract intact, so the consumer-skill `orchestrator-artifacts` mirror needs no update.
- No other call sites, no import/layering changes, no race or resource concerns introduced.

No findings.

REVIEW_PASS
