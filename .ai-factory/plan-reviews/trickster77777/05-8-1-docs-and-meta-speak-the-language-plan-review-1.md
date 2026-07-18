# Plan Review: 8.1 — Docs and meta speak the language

**Plan:** `.ai-factory/plans/trickster77777/05-8-1-docs-and-meta-speak-the-language.md`
**Risk Level:** 🟢 Low

## Context Gates

- **Roadmap linkage — OK.** The plan heading matches the contract line at `.ai-factory/roadmaps/trickster77777.md:49` (`8.1 — Docs and meta speak the language`), whose `Spec:` tag resolves to the spec the plan follows. Scope (files, inflection rule, synonym fix, `process_task()` reflection, protocol-literal/tag/`phase` exclusions, README verify-only) is faithful to the contract line.
- **Contract-line vs ground-truth reconciliation — OK (not a defect).** The roadmap line 49 says "Leave `/milestone-rescue*` (8.2)", but the live docs already carry the conformed skill names `/task-rescue` / `/task-rescue-audit` (`how-it-works.md:25`, `non-convergence.md:37`) — task 8.2 ran doc-first, and the spec was amended per handoff 07. The plan correctly follows ground truth (the actual files), not the pre-8.2 contract phrasing. Code/file wins over the description.
- **ARCHITECTURE.md — in scope, aligned.** It is itself one of the twelve edited files (Task 12); the `## Features` commit-hash preservation is spelled out and matches the spec's ratified decision.
- **RULES.md — absent** (`.ai-factory/RULES.md` does not exist). No rule gate to apply. Not blocking.

## Verification against ground truth

Every line in the plan's line map was cross-checked against a live `grep -rniE "\bmilestone"` over the twelve files. Findings:

- **Line map is complete.** Every bare-word `milestone` occurrence in `docs/*.md`, `CLAUDE.md`, and `.ai-factory/ARCHITECTURE.md` is covered by exactly one task — no occurrence is orphaned, no phantom line is edited. Counts per file match the task line lists (configuration 13, context-model 7, failures-and-halts 7, how-it-works 11, non-convergence 1, phase-sessions 7, target-project 8, test-mode 4, workflow 4, CLAUDE 7+identifier, ARCHITECTURE 5).
- **`how-it-works.md:25` correctly excluded** — the line already reads `/task-rescue` with no bare-word `milestone`; the plan's "no edit at all" instruction is right.
- **`non-convergence.md:37` correctly scoped** — the two skill names are already conformed; only the bare-word `milestone` on the line is in scope.
- **Synonym fix confirmed** — `migrate-to-named-roadmap.md:23` contains "spec notes"; zero `\bmilestone` hits in that file, so the single synonym change is the only edit. The `Spec:` tag on the same line is correctly left legacy.
- **Identifier reflection confirmed** — `CLAUDE.md:85` currently reads `process_milestone()`; the plan renames it to `process_task()`, which matches the post-5.1 code name.
- **§ 4 judgment call confirmed** — `docs/phase-sessions.md` has 2× `кросс-милстоунная` and 0× `межзадачная`; `docs/context-model.md` already uses the native `Межзадачная` term, so aligning to it is precedented, not invented. Verify counts (кросс→0, межзадачная→2) are correct.
- **Config-token corrections confirmed against live code** — `notify.py:15` (`_FAIL_ALERTS = {"task-fail"}`) and `main.py:505` emit `task-fail`/`task`, so `configuration.md:110,125`'s stale `milestone-fail`/`milestone` examples genuinely misdescribe ground truth today. Conforming them is a correction, not a design change — as the plan states.
- **Protocol literals correctly frozen** — `## Deferred observations` (how-it-works:55), `PLAN_REVIEW_PASS`/`REVIEW_PASS` (how-it-works:47,53), and `Spec:`/`Governing spec:` tags are all left byte-identical.
- **README.md** — zero `\bmilestone` hits; verify-only treatment is correct.

## Critical Issues

None.

## Positive Notes

- The plan is an unusually faithful projection of a per-line spec map that was itself verified against the live files — line numbers, inflection outcomes, and exclusions all hold against current ground truth.
- The velar-stem inflection rule (`-ы`→`-и`, `-ов`/`-ами` unchanged) is stated once and applied consistently per task.
- The verify suite (Task 13) is self-checking and includes the non-grep-catchable Cyrillic transliteration (`кросс-милстоунная`) and the hash-preservation check — closing the gaps a plain `\bmilestone` grep would miss.
- Commit messages follow the project convention (imperative, sentence case, no type prefix).

PLAN_REVIEW_PASS
