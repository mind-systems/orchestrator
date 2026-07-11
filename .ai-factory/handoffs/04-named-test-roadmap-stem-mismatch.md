# Handoff — named test-roadmap artifact stem: orchestrator and skills family disagree

## 1. Frame
Multiuser named roadmaps landed on both sides (this repo's tasks 12/13; the skills repo's Phase 4), but a cross-repo verification found they pin **opposite artifact-subdirectory stems for a named test roadmap** — the originating session's context isn't available here; trust these files, not memory.

## 2. Read-first map

### Must-read now (minimal rehydration set)
- `orchestrator/main.py` — `_artifact_subdir()` (~:166): returns `Path(relpath).stem` raw, so `roadmaps/<name>-tests.md` → `<name>-tests`; `_tests_sibling()` (~:158) is what produces that relpath.
- `tests/test_main.py` (~:951–967) — the pinned `_artifact_subdir` mapping: default pair → `None`, `roadmaps/kg-wmservice.md` → `kg-wmservice`; **no test covers the `-tests` sibling** — the raw-stem behavior fell out of the implementation, it was never a decision.
- `~/projects/skills/src/skills/roadmap-prune/SKILL.md` — Step 5, named branch (~:282–285): the ratified opposite — `roadmaps/<name>-tests.md` gives `<stem> = <name>` "(the `-tests` suffix stripped — never the raw basename `<name>-tests`)"; a tests-mode prune sweeps `test-runs/<stem>/`.
- `~/projects/skills/src/skills/orchestrator-artifacts/SKILL.md` — §1 (~:28–29), the protocol engine both repos mirror: subdirectory "keyed by its roadmap file stem … same stem segment under `plan-reviews/`, `reviews/`, `test-runs/`" — one shared segment per roadmap pair.

### Read on demand
- `~/projects/skills/docs/multiuser-roadmaps.md` — the governing spec (Russian): the `-tests`-suffix hard-stop (~line 15; a derived main-roadmap slug ending in `-tests` is rejected — this is what makes unconditional stripping safe) and the ambiguous literal that spawned the divergence (~line 47, "поддиректорию по стему его файла").
- `.ai-factory/specs/12-roadmap-path-setting.md`, `.ai-factory/specs/13-artifact-subdirs.md` — the landed tasks; 13's contract says "the roadmap file's stem" without deciding the test-sibling case.
- `~/projects/skills/.ai-factory/plan-reviews/94-4-7-roadmap-prune-sweep-and-gate-learn-the-per-roadmap-artifact-subdirectories-plan-review-2.md:35` — the source deferred observation that predicted exactly this failure mode and asked for the one-time confirmation.

## 3. Current state

**Done:**
- The confirmation the observation asked for, run 2026-07-12: `_artifact_subdir("roadmaps/<name>-tests.md")` → `<name>-tests` (raw), while the skills family ratified the shared `<name>` segment. Consequence if unfixed: an orchestrator test run on a named roadmap writes `plans/<name>-tests/…` and `test-runs/<name>-tests/…`, a tests-mode prune sweeps `plans/<name>/…` and `test-runs/<name>/…` — the sweep deletes nothing and artifacts accumulate forever.
- Decision (2026-07-12, with the user): **the orchestrator side is the one to fix.** The skills-side reading follows the default-pair analogy (`ROADMAP_TESTS.md` shares `ROADMAP.md`'s flat dirs → `<name>-tests.md` shares `<name>/`), is ratified in two landed skills milestones (4.6, 4.7), and the governing doc's hard-stop reserves the `-tests` suffix — stripping is safe by construction.

**In-flight:**
- This repo has a live orchestrator run mid-milestone (staged plan 19 `resume-adoption-gate`, modified `orchestrator/resume.py`) — unrelated to this handoff; do not disturb its working tree.

**Uncommitted working-tree state:**
- The task-19 run's own staged artifacts and code edits (see `git status`) — not this handoff's concern.

## 4. Next step
Decompose one task into this repo's `.ai-factory/ROADMAP.md` (contract line + spec note): `_artifact_subdir` strips the `-tests` suffix on its non-default branch — `Path(relpath).stem.removesuffix("-tests")` (the default pair already returned `None` above it) — plus unit tests pinning `roadmaps/<name>-tests.md` → `<name>` and an explicit-path sibling (e.g. `custom-tests.md` → `custom`). After the spec file exists, report its path back to the skills repo so the resolution session there can pin the source observation `[routed → <that spec>]` (context: `~/projects/skills/.ai-factory/handoffs/14-prune-gate-unpinned-observations.md`).

## 5. Working discipline
- Plan in chat; the orchestrator implements — never edit `orchestrator/*.py` in the planning session.
- Never commit without explicit permission.
- Artifacts in English regardless of conversation language.

## 6. Error log
- The first cross-repo check concluded "the orchestrator has no stem logic at all" from too-narrow greps over `main.py` (keyword searches for `stem`/`roadmaps` hit only unrelated lines). Correction: grep the mechanism name (`_artifact_subdir`) and read the unit tests — tasks 12/13 had already landed it. Lesson: verify absence by searching for the mechanism, not the concept.

## 8. Domain model spine
- The default pair shares flat dirs (`_artifact_subdir` → `None` for both files) — a named pair analogously shares one `<name>/` segment; a test roadmap never gets its own artifact axis. Don't re-litigate: `~/projects/skills/src/skills/orchestrator-artifacts/SKILL.md` §1.
- `-tests` is a reserved suffix (derivation hard-stop in `~/projects/skills/docs/multiuser-roadmaps.md`), so stripping it never mangles a legitimate main-roadmap stem.

## 10. Cross-cutting contracts / invariants checklist
- Target mapping after the fix: `ROADMAP.md` → `None`; `ROADMAP_TESTS.md` → `None`; `roadmaps/<name>.md` → `<name>`; `roadmaps/<name>-tests.md` → `<name>` (today: `<name>-tests` — the bug).
- One stem keys all four dirs identically: `plans/`, `plan-reviews/`, `reviews/`, `test-runs/`.
- `orchestrator-artifacts` §1 in the skills repo mirrors this code (declared mirrors-invariant) — if the fix lands any mapping other than the one above, that file must change with it.
