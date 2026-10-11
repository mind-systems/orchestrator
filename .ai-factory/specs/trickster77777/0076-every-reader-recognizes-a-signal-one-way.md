# Every reader recognizes a signal through `_has_signal`

**Date:** 2026-10-11
**Source:** the user's go in chat on 2026-10-11, «давай 26 декомпозить» and «го»

Governing spec: [docs/pipeline.md](../../../docs/pipeline.md) — § Completion signals ("A reader recognizes a signal when it stands as an exact line among the file's last five lines…").

## What is true now

This is the tree as "the plan-review signal is held once" leaves it: `protocol.py` defines `PLAN_REVIEW_PASS`, and `agents`, `pipeline` and `resume` import it.

`_has_signal(text, signal)` in `orchestrator/protocol.py` is True when `signal` stands as an exact line, whitespace stripped, among the last five lines of `text`. `PlannerReviewer.review` and `PlanReviewer.review_plan` read the review file through it, so a review that ends with `REVIEW_PASS` or `PLAN_REVIEW_PASS` and then a stray line is accepted live.

These readers test `.read_text().strip().endswith(...)` instead:

- `process_task`'s plan-review safety guard in `orchestrator/pipeline.py`, on the latest plan review, against `PLAN_REVIEW_PASS`; when it fails it raises `PipelineStopError`;
- `_validate_sidecar_step`'s `plan_reviewed` check in `orchestrator/resume.py`, on any plan review, against `PLAN_REVIEW_PASS`;
- `_detect_step` in `orchestrator/resume.py`, on the latest plan review against `PLAN_REVIEW_PASS`, and on the latest verify output against `verify.pass_signal`.

So a plan review that passes with a stray line after the signal gets past the live check, then stops the run at the guard; and on resume the same file reads as a failed plan review, and a verify output in that shape reads as unfinished. `_validate_sidecar_step`'s docstring says a plan-review file "ends with PLAN_REVIEW_PASS".

## What must be true after

The guard in `pipeline`, the `plan_reviewed` check in `_validate_sidecar_step` and the checks in `_detect_step` call `_has_signal(text, signal)` on the file's text, the signal being `PLAN_REVIEW_PASS` or `verify.pass_signal` as each reads today. `pipeline` and `resume` import `_has_signal` from `protocol`.

`_validate_sidecar_step`'s docstring states that a plan-review file carries `PLAN_REVIEW_PASS` as an exact line among its last five lines.

After the change every reader recognizes a signal as the live reviews do, as an exact line among the file's last five lines.

Tests in `tests/test_main.py`, beside the `_detect_step` tests, each with a stray line after the signal:

- a latest verify output ending in `REVIEW_PASS` and a stray line resolves to `done`;
- a latest plan review ending in `PLAN_REVIEW_PASS` and a stray line resolves to `implement`, the step `_detect_step` returns for a passing plan review in a clean working tree.

They exist because a resume that misreads a passing artifact silently repeats finished work. The guard gets no test: it fails loudly with `PipelineStopError`.

## What breaks on contact

- The existing plan-review and verify fixtures end with the signal as their last line, so every existing resume and pipeline test resolves as before.
- `docs/pipeline.md` § Completion signals already states the last-five-lines reading, so no doc changes.
