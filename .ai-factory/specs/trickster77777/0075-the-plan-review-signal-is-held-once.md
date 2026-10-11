# The plan-review signal is held once

**Date:** 2026-10-11
**Source:** the user's go in chat on 2026-10-11, «давай 26 декомпозить» and «го»

Governing spec: [docs/pipeline.md](../../../docs/pipeline.md) — § Completion signals ("A reader recognizes a signal when it stands as an exact line among the file's last five lines…").

## What is true now

This is the tree as the tasks above it leave it: `protocol.py` holds `_has_signal`, `_has_escalation` and the sidecar helpers, and `agents`, `pipeline` and `resume` import from it.

`PLAN_REVIEW_PASS` is spelled out as a literal in these readers:

- `PlanReviewer.review_plan` in `orchestrator/agents.py`: the prompt sentence "end the review file with PLAN_REVIEW_PASS on its own line", and the `_has_signal(review_text, "PLAN_REVIEW_PASS")` check at its end;
- `process_task`'s plan-review safety guard in `orchestrator/pipeline.py`, an `endswith` on the latest plan review;
- `_validate_sidecar_step`'s `plan_reviewed` check in `orchestrator/resume.py`, an `endswith` on any plan review;
- `_detect_step` in `orchestrator/resume.py`, an `endswith` on the latest plan review.

`REVIEW_PASS` and `TEST_PASS` are held once on their verify kinds, as the `pass_signal` of `REVIEW_VERIFY` and `TEST_RUN_VERIFY` in `agents.py`. The prompt files under `orchestrator/prompts/` name the protocol signals as literals.

## What must be true after

`orchestrator/protocol.py` defines `PLAN_REVIEW_PASS = "PLAN_REVIEW_PASS"`. It lives there, not in `agents`, because `resume` reads it and would otherwise import `agents`, the edge the layer map removes.

`agents`, `pipeline` and `resume` import `PLAN_REVIEW_PASS` from `protocol`. `review_plan`'s prompt sentence interpolates it and its `_has_signal` call takes it; the guard in `pipeline` and the checks in `_validate_sidecar_step` and `_detect_step` take it where they wrote the literal. Each check keeps the form it has: `endswith` stays `endswith`, `_has_signal` stays `_has_signal`.

`REVIEW_PASS` and `TEST_PASS` stay on their verify kinds. The prompt files under `orchestrator/prompts/` keep the protocol literal.

The change is behaviour-neutral: the plan reviewer's prompt text and every reader's result are as before.

## What breaks on contact

- Nothing in the tests: their fixtures write the signal into review files as text, and the prompt text the planner reviewer receives is unchanged.
- `docs/pipeline.md` names `PLAN_REVIEW_PASS` as the protocol's signal and states no home for it, so it stays true.
