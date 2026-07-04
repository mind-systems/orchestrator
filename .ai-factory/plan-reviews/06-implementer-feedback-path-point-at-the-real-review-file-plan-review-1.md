## Plan Review Summary

**Plan:** Implementer feedback path — point at the real review file
**Files targeted:** `orchestrator/agents.py`, `orchestrator/main.py`, `orchestrator/prompts/implementer.md`, `CLAUDE.md`, `docs/how-it-works.md`, `docs/test-mode.md`
**Risk Level:** 🟡 Medium

The plan is well-scoped and its codebase assumptions are almost entirely accurate. I verified every cited line number and naming convention against the current source:

- `agents.py:384` signature, `386-390` continuing branch, `392-396` `patches_note` scan block — all match. ✓
- `main.py:257/261` (`patches_dir` + mkdir), `369` implement call — match. ✓
- `main.py:519/522` (test-mode `patches_dir` + mkdir loop), `627` implement call, `642-644` copy-bridge — match. ✓
- Test-run naming at `main.py:633` is `-test-{iteration}.txt`. The plan (Task 3) explicitly corrects the spec's loose `-test-run-{n}.md` form to the real `-test-{n}.txt`. Good catch — this would otherwise have produced a dead pointer. ✓
- `docs/how-it-works.md:9` and `:45`, `docs/test-mode.md:19`, `CLAUDE.md:68` — all exist as described. ✓
- Resume logic: I traced `_detect_milestone_step` / `_detect_test_milestone_step`. Every path that returns `("implement", n)` guarantees the `review-{n-1}` / `test-{n-1}` file already exists (it's the failed artifact that triggered re-implementation), and `iteration == 1` returns `None`. The `iteration - 1` feedback pointer is therefore always valid on resume. ✓

### Context Gates
- **Architecture (`.ai-factory/ARCHITECTURE.md`):** not consulted as a boundary source here; the change is confined to the existing agent/file-protocol seam. No boundary violation. OK.
- **Rules / project CLAUDE.md:** see Critical Issue #2 — the file-protocol change carries a stated cross-repo obligation the plan does not acknowledge.
- **Roadmap:** milestone `06` linkage is consistent with the plan heading. OK.

### Critical Issues

**1. Task 3's acceptance criterion is unmet by the plan's own tasks — two `patches` occurrences in `agents.py` are never removed.**
Task 3 states: *"After this task, `git grep -n patches -- 'orchestrator/*.py'` must return nothing."* But `git grep` currently also matches two spots that **no task touches**:
- `agents.py:369` — the `Implementer` class docstring: `"""Implements the plan, then applies fixes from patches. Same session."""`
- `agents.py:386` — the inline comment `# Continuing — apply fixes from patches` (Task 1 rewrites the *prompt* on lines 387-390 but does not mention the comment on line 386).

As written, an implementer who follows Tasks 1–3 literally will leave both in place, and Task 3's verification (`git grep … must return nothing`) will **fail**. Fix: extend **Task 1** to also (a) reword the class docstring on line 369 to drop "patches" (e.g. *"Implements the plan, then applies the review feedback for the current iteration. Same session."*), and (b) update/remove the line-386 comment. Then the grep gate is achievable.

### Non-Blocking Notes (WARN)

**2. Downstream consumer-skill obligation not acknowledged.** The project `CLAUDE.md` states: *"Consumer skills in `~/projects/skills` mirror this file protocol … any change to the protocol (directory layout, artifact naming, PASS signals, sidecar fields, review-section format) must be reflected there."* Retiring `patches/` is a directory-layout change to that protocol. Editing the other repo is reasonably out of scope for this milestone, but the plan should at least note the obligation so the `orchestrator-artifacts` engine (and skills like `milestone-rescue`, which reads `patches/`) get updated separately — otherwise the contract silently drifts.

**3. Docs language.** `docs/how-it-works.md` and `docs/test-mode.md` are written in Russian. Task 5 describes the rewordings in English ("reword to say the reviewer's review file…"). That is intent, not literal copy — the implementer must keep the rewritten sentences in **Russian** to match surrounding docs. Worth making explicit in Task 5 so the implementer doesn't inject English prose into a Russian file.

### Positive Notes
- Line-level precision throughout; the plan reads like it was written against the actual source, not from memory.
- The spec-vs-reality naming correction in Task 3 (`-test-{n}.txt`) is exactly the kind of thing that silently breaks a feedback pointer — catching it in the plan is excellent.
- Dependency ordering (Task 1 before 2/3/4; Tasks 2,3 before 5) and the two-commit split are clean and correct.
- Correctly instructs *not* to invent a new directory and *not* to claim leftover target-project `patches/` dirs are cleaned (they aren't) — avoids two easy overreach mistakes.

Address Critical Issue #1 (and ideally fold in notes #2–#3) and the plan is ready.
