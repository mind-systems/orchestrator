# Plan: Prompts/docs: drop the sweep-guard clause; specs/ naming in docs

## Context
Remove the redundant negative depth guard ("do not sweep the notes directory or read specs of unrelated tasks") from the follow-mentions block of the planner/test-planner/reviewer prompts, and update docs prose to name the spec-note home as the pair `specs/` (current) / `notes/` (legacy), served via the literal path in the `Spec:` tag. Prompt + docs only — no Python changes.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Prompts — drop the sweep-guard clause

- [x] **Task 1: Drop the guard half from `planner.md` follow-mentions block**
  Files: `orchestrator/prompts/planner.md`
  In the "Follow mentions" block (Step 0), the last bullet currently reads:
  `- Follow only links reachable from your milestone; do not sweep the notes directory or read specs of unrelated tasks.`
  The `Follow only links reachable from your milestone` half is the positive depth-self-limit and stays; the prohibition half is fused into the same sentence and must go. Rewrite the bullet to:
  `- Follow only links reachable from your milestone.`
  Delete nothing else. The other three bullets and the intro line stay word-for-word. Do NOT replace the removed clause with any generic guard.

- [x] **Task 2: Drop the guard half from `test-planner.md` follow-mentions block**
  Files: `orchestrator/prompts/test-planner.md`
  Identical edit to Task 1. The Step 0 "Follow mentions" block has the same bullet:
  `- Follow only links reachable from your milestone; do not sweep the notes directory or read specs of unrelated tasks.`
  Rewrite it to:
  `- Follow only links reachable from your milestone.`
  Leave the rest of the block untouched; no generic guard replacement.

- [x] **Task 3: Confirm `reviewer.md` gate carries no sweep/depth prohibition** (depends on Task 1)
  Files: `orchestrator/prompts/reviewer.md`
  The Context Gates section already ends its follow-mentions bullet with "findings are judged against this tree, not against the roadmap line alone" and carries no "do not sweep" / "unrelated tasks" prohibition. Grep the file for any sweep/depth prohibition; if one is present, delete only that clause (keeping "findings are judged against the tree lifted from the milestone's line"). If none is present — the expected current state — leave the file unchanged. Do NOT add a generic guard.

### Phase 2: Docs — specs/ naming

- [x] **Task 4: State the specs/notes pair in docs and verify no Python `notes/` literals** (depends on Task 3)
  Files: `docs/context-model.md`, `docs/target-project.md`
  Grep-sweep `docs/` (`grep -rn "нот\|notes\|specs" docs/`) for prose that names the directory holding spec notes as its home. Phrase-level edits only — do not rewrite pages, and keep the existing Russian wording/style.
  - `docs/context-model.md`: at the `Spec:`-тег bullet (currently "…путь к спек-ноте задачи; нота ссылается на смежные ноты, и агент идёт по этим ссылкам. Паутина нот — главный носитель межзадачных связей."), add a short clause stating the pair: спек-ноты живут в `specs/` (текущее имя) или `notes/` (легаси); оркестратору это безразлично — агент идёт по буквальному пути из `Spec:`-тега. Insert as a phrase, not a new section.
  - `docs/target-project.md`: check whether the spec-note directory is named as its home. It currently is not named — if the sweep confirms no such naming, leave the file unchanged; only add the pair if a naming is actually present.
  - Verify by grep that `agents.py`, `main.py`, `roadmap.py` contain no `notes/` (or `specs/`) literals (`grep -rn "notes/\|specs/" orchestrator/*.py`) — none expected. Make NO Python changes; this is a verification only. Do NOT add any migration instructions for target projects.
