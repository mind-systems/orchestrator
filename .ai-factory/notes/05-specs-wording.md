# Prompts/docs: drop the sweep-guard clause; specs/ naming in docs

**Date:** 2026-07-03
**Source:** conversation context (notes-are-specs review)

## Key Findings

- The follow-mentions block (planner/test-planner Step 0, reviewer gate) carries a negative depth guard: "Follow only links reachable from your milestone; **do not sweep the notes directory** or read specs of unrelated tasks." The guard is redundant over-protection: the positive rule — lift the tree from your contract line by following mentions — self-limits depth **by construction** (unrelated specs have no edge from your line), and the philosophy is now threaded through the project CLAUDE.mds as well. Worse, the guard names a directory (`notes/`), and with the lazy `notes/`→`specs/` migration a name-bound prohibition is exactly the kind of duplicated rule that drifts.
- Fix: **delete the guard clause, replace it with nothing.** Keep the positive follow-mentions rule word-for-word.
- Separately, docs prose that names `notes/` as *the* home of spec notes needs the new pair stated once: `specs/` (current), `notes/` (legacy, still served via the tags' literal paths). Nothing in Python knows either path — agents follow the literal path in the milestone line; behavior is already correct.

## Details

- **`planner.md` + `test-planner.md`** (follow-mentions block): remove the sweep-guard sentence/clause ("Follow only links reachable…; do not sweep the notes directory or read specs of unrelated tasks") — the remaining block states the positive rule only. If the "reachable from your milestone" half is fused into the same sentence, keep the positive half and drop the prohibition half.
- **`reviewer.md`**: same — if its gate carries a sweep/depth prohibition, delete it; the gate keeps only "findings are judged against the tree lifted from the milestone's line".
- **Docs grep-sweep** (`grep -rn "notes" docs/`): `context-model.md` ("паутина нот" and any "spec notes live in notes/" phrasing), `target-project.md`, others — where the directory is named as the home of specs, state the pair: `specs/` current, `notes/` legacy via tags. Phrase-level sweep, do not rewrite pages.
- Verify by grep that `agents.py`/`main.py`/`roadmap.py` contain no `notes/` literals (none expected). No Python changes.

## What NOT to do

- Do not replace the deleted guard with a generic one ("do not sweep the spec directories") — no negative guard at all; the positive rule is the whole protection.
- Do not touch the rest of the follow-mentions block — the positive rule stays word-for-word.
- Do not instruct any migration of target projects — old tags stay valid by design.
