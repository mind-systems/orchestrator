# `## Deferred observations` — a standardized home for non-blocking reviewer findings

**Date:** 2026-07-04
**Source:** conversation context (milestone-48 review-margins analysis)

## Key Findings

- Reviewers routinely produce a second layer of output besides blocking findings: observations they verified as real but consciously deprioritized against the current milestone — ad-hoc "Note A/B", "Finding N — INFO", markers like "latent", "forward risk", "no action needed this milestone", "flagging so Phase 3a accounts for it", even "Surface this to the orchestrator". Live evidence: tradeoxy_gui milestone-48 reviews, where Finding 4 and Note B correctly predicted concrete Phase-3a failures.
- The pipeline binarizes reviews into pass/fail (`_has_signal` on `PLAN_REVIEW_PASS`/`REVIEW_PASS`); non-blocking notes are read by no one on success and are deleted by `roadmap-prune` later. The better a milestone converges, the more certainly its margins are lost. There is no delivery channel to the downstream phases those notes address.
- Fix (prompt-only, this repo's half of the channel): standardize the layer as a `## Deferred observations` section in `prompts/reviewer.md`, so it becomes machine-sweepable. The harvesting consumer (a step in the `roadmap-prune` skill sweeping both `plan-reviews/` and `reviews/` before artifact deletion) lives in the skills repo — out of scope here.

## Details

- **`prompts/reviewer.md` — Output Format:** add `## Deferred observations` to the review template, after the findings sections and **before** the signal line. Entry shape:
  - `- Affects: <phase / spec-note path / "unknown"> — <one-paragraph observation>`
  - Rule for the reviewer: everything you noticed and verified but consciously did not block goes here, each with an addressee. If nothing was deferred, omit the section.
- **Deferral criterion — scope, not severity (the anti-laundering guard):** the section must NOT become a dumping ground that softens the review. State the rule explicitly in the prompt: an observation may be deferred **only if its fix lies outside the current milestone's scope** — a different phase, a future consumer that does not exist yet, a file boundary the plan does not touch. Anything introduced by the current diff, or fixable within the milestone's boundary, is a **finding regardless of severity** — down to cosmetics (a stale comment in a changed file is a finding, not a deferred observation). Operational test for the reviewer: "if the implementer could fix this on the next iteration without leaving the milestone's file boundary or contradicting the plan — it is a finding." This codifies the strict reviewer's existing behavior (live calibration from tradeoxy_gui milestone 48: a LOW stale-comment in a changed file was filed as a Finding, while a higher-impact `ackFor$` hang was correctly deferred because its only consumer arrives in Phase 3a).
- **Role-neutral wording:** one prompt file serves both reviewers — `PlanReviewer` uses `reviewer.md` as its entire system prompt, `PlannerReviewer` concatenates planner + reviewer (`agents.py:247,322`). The section text must not say "code" or "plan"; it applies to both review types, so both `plan-reviews/` and `reviews/` files gain the section from this single edit.
- **PASS interaction (critical):** extend the REVIEW_PASS rules with an explicit clause — deferred observations are **not findings**; a review whose only content is deferred observations still ends with `REVIEW_PASS` (same for `PLAN_REVIEW_PASS`). Without this clause the section would silently raise the convergence bar, which is exactly what it must not do: the pass/fail binarization is what makes the loop converge, and the section is a delivery channel, not a gate.
- **Status field reserved for downstream tooling:** the reviewer never writes status markers on entries — anything after the observation text is reserved for downstream consumers (the skills-repo harvest/audit tools append machine-readable processing statuses there, e.g. `promoted → <spec>`). A fresh review file always arrives with unmarked entries; state this in the prompt so the reviewer does not imitate markers it may see in earlier review files of the same milestone.
- **Signal detection untouched:** the section precedes the signal line, and `_has_signal` checks the last line — no Python changes; verify by grep that `agents.py`/`main.py` are untouched.
- **Docs:** mention the section in `docs/how-it-works.md` where the file protocol / review files are described (current-state description only).
- **Verify:** run a milestone where the reviewer has a genuine non-blocking observation; the review file must show it under `## Deferred observations` with an `Affects:` target, and the review must still PASS if no blocking findings exist.

## What NOT to do

- Do not raise the severity of deferred observations or make them gate anything — the entire design hinges on them staying non-blocking.
- Do not let severity drive deferral — "it's only LOW" is never a reason to defer; only out-of-scope is. The two axes are independent by design.
- Do not have the reviewer write, copy, or update status markers on deferred-observation entries — including when re-reviewing a milestone whose earlier review files already carry downstream marks. The status field belongs to downstream tooling exclusively.
- Do not implement the harvest step here — `roadmap-prune` belongs to the skills repo; this task only produces the standardized source format.
- Do not change the `Final Output Rule` (reviewer outputs only `done`) or the placement rules of the PASS signals.
