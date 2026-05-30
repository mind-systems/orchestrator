# Code Review: 21-remove-refactor-and-review-cli-flows

## Summary

Pure deletion milestone. The diff removes exactly what the plan called for and nothing more. I read every changed file in full, ran the smoke check, and grep-verified that no live reference to the removed entities survives.

**Risk Level:** 🟢 Low — pure dead-code excision; smoke check passes; all callers of removed code are themselves removed.

## What was deleted

| Entity | File | Verified gone |
|--------|------|---------------|
| `RefactorPlanner` class (90 lines) | `orchestrator/agents.py` | ✓ |
| `PlannerReviewer.patch()` method | `orchestrator/agents.py` | ✓ |
| `process_refactor_milestone()` | `orchestrator/main.py` | ✓ |
| `review_plan()` | `orchestrator/main.py` | ✓ |
| `_refactor_loop()` | `orchestrator/main.py` | ✓ |
| `run_refactor()` | `orchestrator/main.py` | ✓ |
| `run_review()` (incl. `_already_passed`, inner `loop`) | `orchestrator/main.py` | ✓ |
| `RefactorPlanner` from import on line 13 | `orchestrator/main.py` | ✓ |
| `("review", ...)` and `("refactor", ...)` subcommand tuples | `orchestrator/main.py` | ✓ |
| `if args.command == "review":` and `elif args.command == "refactor":` dispatch branches | `orchestrator/main.py` | ✓ |
| `orchestrator/prompts/refactor-planner.md` | filesystem | ✓ |
| `docs/refactor-mode.md` | filesystem | ✓ |
| `review` / `refactor` rows in CLAUDE.md Commands | `CLAUDE.md` | ✓ |
| `RefactorPlanner` bullet in CLAUDE.md Architecture | `CLAUDE.md` | ✓ |
| `process_refactor_milestone()` reference + `refactor verify` mention in CLAUDE.md Key constants | `CLAUDE.md` | ✓ |
| `review` / `refactor` rows + broken `docs/refactor-mode.md` link in README.md | `README.md` | ✓ |
| Russian-language refactor references in `docs/configuration.md` | `docs/configuration.md` | ✓ |

## Correctness checks

**1. Dispatch `elif`→`if` conversion was applied correctly.** The plan flagged the `elif args.command == "test":` trap. `main.py:626` is now `if args.command == "test":`, with `else: run_implement(...)` and both `except` blocks intact. No `SyntaxError`.

**2. Import line has no orphan name.** `main.py:13` reads exactly `from .agents import Implementer, PipelineStopError, PlannerReviewer, PlanReviewer, RateLimitError, TestRunner, _read_sessions, _write_session` — `RefactorPlanner` is gone. `from . import state` on line 15 is preserved (still used by `_handle_sigint`).

**3. No orphan call sites.** `grep -nri 'RefactorPlanner\|process_refactor_milestone\|_refactor_loop\|run_refactor\|run_review\|refactor-planner'` across `orchestrator/`, `docs/`, `CLAUDE.md`, `README.md` returns zero hits. The only matches are inside `.ai-factory/` artifacts (historical plans, notes, plan-reviews) which are intentionally not touched — they're commit-anchored history.

**4. `PlannerReviewer.patch()` removal is safe.** Its sole caller was `review_plan()` (also removed); confirmed by full-file grep.

**5. Surviving infrastructure is untouched.** `_detect_milestone_step()`, `_detect_test_milestone_step()`, `_run_loop`, `_implement_loop`, `_test_loop`, `process_milestone`, `process_test_milestone`, `PlannerReviewer.plan/review`, `PlanReviewer.review_plan`, `Implementer.implement`, `TestRunner.run`, `_with_caffeinate`, `_handle_sigint`, `state.stop_requested`, `_read_sessions`, `_write_session`, `PipelineStopError`, `RateLimitError` all read identically to the prior file. The two `except` branches in `cli()` still catch both exceptions.

**6. PEP-8 spacing preserved.** Two blank lines between every pair of top-level defs in `main.py` and between every pair of top-level classes in `agents.py`, matching the rest of the file. Verified at the deletion boundaries (e.g. `process_milestone` → `_with_caffeinate`, `_implement_loop` → `run_implement`, `class PlannerReviewer` → `class PlanReviewer`, `class Implementer` → `class TestRunner`).

**7. Documentation language preserved.** `docs/configuration.md` edits stayed in Russian, matching the file's existing language. CLAUDE.md and README.md edits stayed in their respective languages.

**8. ROADMAP.md milestone formatting unchanged.** The new entry was appended in the standard `- [ ] **Title** — Description` format with a backlink to `notes/07`.

## Smoke check

```
$ uv run orchestrator --help
usage: orchestrator [-h] {implement,test} ...

AI orchestrator — plan, implement, review from roadmap

positional arguments:
  {implement,test}  Command to run
    implement       Plan and implement milestones
    test            Write tests for milestones (uses test-planner prompt)
```

Exit code 0. Only `implement` and `test` appear. No `ImportError`, no `SyntaxError`, no `AttributeError`. `python -c "import orchestrator.main; import orchestrator.agents"` also passes.

## Observations (non-blocking, pre-existing)

These are not introduced by this milestone — they were already in the codebase before the change — but worth flagging in case any future cleanup pass wants to mop them up:

1. **`ParseResult` is imported but unused** in `orchestrator/main.py:14` (`from .roadmap import ParseResult, mark_done, mark_skipped, parse_roadmap`). Has been unused since well before this milestone. Removing it would tighten the import, but it's not a regression here.

2. **README.md docs-index table lacks a header row** (lines 41–45). The first table ("Команды") has a proper `|---|---|` separator; the second one (the docs index) is just naked rows. Pre-existing — the deleted `docs/refactor-mode.md` row had the same shape. Not a regression.

3. **README.md intro at line 5 calls the pipeline "пятиступенчатый" (five-step) but lists four stages** (Planner, PlanReviewer, Implementer, Reviewer). Pre-existing inconsistency.

4. **CLAUDE.md:54 says `_run_claude()` uses `--output-format json`** but `agents.py:70` actually uses `--output-format stream-json`. Pre-existing documentation drift.

None of these are caused by this milestone and none affect runtime behavior of the `implement` or `test` flows.

## Verdict

The deletion is complete, atomic (single commit boundary leaves no broken intermediate state), surgically scoped (only refactor/review code touched), and verified by a working `--help` invocation. No bugs introduced.

REVIEW_PASS
