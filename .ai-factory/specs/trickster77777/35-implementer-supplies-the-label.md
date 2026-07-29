# Implementer: supply the label, not only the ban

**Date:** 2026-07-29
**Source:** conversation context (cross-repo follow-up to `.ai-factory/handoffs/05-code-cites-plan-layer-orchestrator-side.md` and `.ai-factory/handoffs/08-plan-layer-citations-recur-in-docstrings.md`)

## Problem today

`orchestrator/prompts/implementer.md` forbids plan-layer citations at two sites — the DON'T-list bullet (~:108) and Critical Rule 7 (~:128) — but names only "code/test comments" as the construct, and only `Phase N` / note number / `ROADMAP`/`Plan` reference / `.ai-factory/` path as the shapes. Neither list matches what actually leaks: the construct that leaks is the module docstring (a Python triple-quoted string, not a comment, and not a construct either site names), and the shape that leaks is `# Task N:`, transcribed straight from the plan's own `- [ ] **Task 1: <subject>**` header format prescribed at `planner.md:96` and `test-planner.md:96`. A rule that never names the construct or the shape actually in play has no purchase on the leak, however well-intentioned its ban.

The mechanism is not disobedience. A generated test file has no intrinsic structure of its own the way a production file does (a production section comment names something that exists in the code); the implementer walks the plan's numbered task list to write the file, and the coordinate it is walking becomes the section label because nothing else was supplied. Banning the citation without giving the implementer another label to reach for predictably fails — it removes the only vocabulary offered and replaces it with nothing.

## The change

At both sites in `orchestrator/prompts/implementer.md`:

- Widen the construct list from "code/test comments" to comments, docstrings, and module headers.
- Add `Task N` and `task N.M` to the forbidden-shape list, alongside the existing `Phase N` / note number / `ROADMAP`/`Plan` reference / `.ai-factory/` path.
- Add the positive replacement the current wording lacks: a test file's section comments and module docstring are labelled by the behavior under test, not by the plan coordinate that produced them — the plan's `**Task N:**` headers are scaffolding for the implementer's own walk through the work, never content to transcribe into the file it writes.

## Guards

- Prompt-only, `orchestrator/prompts/implementer.md` alone.
- Do **not** change the `**Task N:**` plan-list format in `planner.md` or `test-planner.md` — the plan layer citing itself is legitimate, and task 7.1 froze that format deliberately.
- Do **not** add a check to `reviewer.md` — a reviewer gate was considered for this phase and explicitly declined.
- Do **not** sweep any existing citation in the codebase — task 19.2 owns the one instance in scope; the remaining `# Task N:` comments stay untouched, deliberately, as cross-repo evidence.

## Verify

- `grep -niE "docstring" orchestrator/prompts/implementer.md` hits both the DON'T-list bullet and Critical Rule 7.
- `grep -nE "Task N" orchestrator/prompts/planner.md orchestrator/prompts/test-planner.md` is unchanged from today (this task does not touch either file).

## What NOT to do

- Do not touch `planner.md`, `test-planner.md`, or `reviewer.md`.
- Do not touch any file under `tests/` or `orchestrator/*.py` — this is a prompt-only change.
- Do not remove or rewrite the existing shape list; extend it.
