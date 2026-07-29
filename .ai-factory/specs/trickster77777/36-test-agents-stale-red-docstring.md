# `test_agents.py`: a stale RED docstring that misstates the code

**Date:** 2026-07-29
**Source:** conversation context (cross-repo follow-up to `.ai-factory/handoffs/05-code-cites-plan-layer-orchestrator-side.md` and `.ai-factory/handoffs/08-plan-layer-citations-recur-in-docstrings.md`)

## Problem today

`tests/test_agents.py:260` reads `# Task 5: RED case -- semver ordering (fixed in task 2.2)`. `2.2` is a roadmap coordinate whose phase is already pruned — the roadmap now opens at `### Phase 3` — so the citation dangles today and will turn into a false resolution the moment `roadmap-prune`'s number reuse hands `2` to some later, unrelated direction.

Worse, the docstring at lines 265–268 still states the assertion "is expected to fail until the sort is semver-aware", but task 2.2 (commit `693a6a5`) already made the sort semver-aware, and the test passes today — verified: `uv run pytest tests/test_agents.py::test_resolve_claude_semver_ordering_picks_true_latest` → 1 passed. A durable test file currently asserts something false about the code it tests: it narrates the plan's timeline instead of describing current behavior, and the timeline has since moved past it.

## The change

- Rewrite the section comment (`test_agents.py:260`) to name the behavior the section groups — no plan coordinate, no "fixed in task N" aside.
- Rewrite the docstring (`test_agents.py:265–268`) to state what the test asserts about the code's current behavior, self-contained — drop the "expected to fail until…" framing entirely, since the behavior it describes is already true.

## Guards

- Comment and docstring text only. No change to the assertion, the test name, any fixture, any import, or any logic.
- Leave the other 17 `# Task N:` comments in `test_agents.py` and all 27 across the other test files (`test_main.py`, `test_roadmap.py`, `test_runtime.py`, `test_notify.py`) untouched — they are deliberately deferred as cross-repo evidence, not an oversight of this task.

## Verify

- `uv run pytest` is green.
- `test_resolve_claude_semver_ordering_picks_true_latest` still passes.
- Exactly one `# Task` comment is removed from `test_agents.py` (18 → 17); no other test file changes.

## What NOT to do

- Do not touch any other `# Task N:` comment in this file or any other test file.
- Do not touch the assertion, fixtures, or imports in this test.
- Do not touch `orchestrator/prompts/*` or any production code — this task is confined to `test_agents.py`'s comment and docstring text.
