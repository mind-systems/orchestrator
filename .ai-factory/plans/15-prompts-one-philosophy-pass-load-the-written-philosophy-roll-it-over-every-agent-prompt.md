# Plan: Prompts: one philosophy pass — load the written philosophy, roll it over every agent prompt

## Context
Roll the skills repo's written context-tree / grounding philosophy over all four agent prompts: extend the planners' Follow-mentions block to recurse **down to the leaf (code)**, give the implementer a **ground-truth-wins / escalate-don't-invent** discipline, and audit the reviewer — confirming its tree gate and full-file-read stay conformant, and adding the one minimal line that teaches it to read the implementer's new `DEVIATION:`/`BLOCKED:` annotations as deliberate signals rather than defects (the annotation protocol is introduced here, so its reader — `reviewer.md`, edited in this same milestone — is given here too). Prompts only — no Python, no docs; pass-signal and `done`-output contracts untouched.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Ground in the philosophy

- [x] **Task 1: Read the philosophy sources before editing any prompt (hard read-first mandate)**
  Files: (read-only) `~/projects/skills/docs/context-tree.md`, `~/projects/skills/docs/skill-composition-model.md`, `~/projects/skills/src/global/CLAUDE.md` (§ "Grounding claims"), and this milestone's spec `.ai-factory/specs/11-prompts-philosophy-pass.md`.
  Read all four in full first. The three rules the following edits must mirror: (a) **the leaf is code** — a chain that stops at a doc/note has not reached ground truth; recurse along named edges to the source file. (b) **ground truth wins** — the file on disk overrides any description of it (plan, spec, memory). (c) **pin contracts/values, escalate rather than invent** — a smart executor confidently fabricates the specifics it lacks; the counter-default is to flag contradictions and blocks, not fill them silently. No file output for this task — its deliverable is that Tasks 2–4 are worded to embody these rules. Check the box once the sources are read.

### Phase 2: Roll the philosophy over the prompts

- [x] **Task 2: Planners — extend the mirrored Follow-mentions block to the leaf** (depends on Task 1)
  Files: `orchestrator/prompts/planner.md`, `orchestrator/prompts/test-planner.md`
  In **both** files, replace the existing `**Follow mentions.**` block (`planner.md` lines 21–25, `test-planner.md` lines 18–22) with the identical text below. The block must be **byte-for-byte identical** in the two files (`diff` of the extracted blocks → empty). It keeps the width limiter and the `Governing spec:` read verbatim in meaning, adds the explicit recursion-to-the-leaf rule and the attribution rule:

  ```markdown
  **Follow mentions.** The milestone line and everything it references form the context tree for this task — walk it to the leaf:
  - Read the note behind the milestone's `Spec:` tag — it is the full specification; the line is its header.
  - Then read what that note itself names, and what *those* name in turn — recurse down named edges (a note referencing another note, a note naming a doc), never stopping one hop short. **The leaf is code:** when a note names a source file, open the file — it is ground truth; its description drifts.
  - Reading your milestone's line in the roadmap, check its phase header — if it names `Governing spec:` documents, read them.
  - Follow only links reachable from your milestone — depth along named edges, never a sweep across unrelated branches.
  - A reference you deliberately don't open, attribute it ("per the spec…") — never paraphrase it from memory.
  ```

  Do not touch anything else in Step 0 (the `ARCHITECTURE.md`/`RULES.md` reads, the "Use this context when" list in `planner.md`, the surrounding steps). Leave every other block — plan format, commit rules, `done` output — untouched.

- [x] **Task 3: Implementer — add the ground-truth / escalate-don't-invent discipline** (depends on Task 1)
  Files: `orchestrator/prompts/implementer.md`
  Two edits, both prompt-only; no new artifacts, no interactivity (headless stays headless — annotations ride the plan file, which is already the progress source of truth the reviewer reads).

  (a) Insert a new rule block into the existing DO/DON'T register — place it immediately after the `### DON'T:` list and before `## Critical Rules`:

  ```markdown
  ### Ground truth over the plan

  The plan is a description written before implementation; the files on disk are the truth. When they disagree, or the plan is silent where a decision is required:

  - **Ground truth wins** — a stale path, wrong signature, or mismatched value in the plan is implemented per the file, not per the plan.
  - **Fix and flag, never silently deviate** — after implementing per ground truth, annotate the task's line in the plan file: `DEVIATION: <plan said / file showed / done>`. The checkbox is marked as normal once the task is complete.
  - **Escalate ambiguity, don't invent** — a task blocked by a missing decision the plan never made gets `BLOCKED: <the missing decision>` on its line; its checkbox stays unchecked, and independent tasks continue. An unfinished honest plan beats a finished invented one.

  Both annotations ride the plan file — no new files, no interactive prompts. They are for genuine contradictions and blocks, not running commentary.
  ```

  (b) Add one rule to the `## Critical Rules` numbered list. It must sit **before** the existing "All output must be in English" rule (that rule stays last): insert the new rule as item `6.` and renumber the current `6. All output must be in English` to `7.`.

  ```markdown
  6. **Ground truth wins over the plan** — implement a stale/wrong plan detail per the file and flag it with `DEVIATION: <plan said / file showed / done>`; on a missing decision, mark the task `BLOCKED: <the missing decision>` and leave it unchecked rather than inventing.
  ```

  Leave the checkbox-update rules, NO-tests / NO-reports rules, and the workflow steps untouched.

- [x] **Task 4: Reviewer — audit the tree gate, teach it to read the new annotations** (depends on Tasks 1 & 3) — Audit: conformant, no change. The tree gate (line 19) judges findings against the full mentions tree (not the roadmap line alone), and the full-file-read rule (line 9) already reaches ground-truth code directly by reading each changed/new file in full — the two mechanisms together already satisfy "the leaf is code" without needing the gate text itself to spell out recursion.
  Files: `orchestrator/prompts/reviewer.md`
  Two parts.

  (a) **Audit for conformance (expect no change).** Check two surfaces against the philosophy sources from Task 1: the Context-Gates **tree gate** (`reviewer.md` line 19 — "Follow mentions from the milestone under review… findings are judged against this tree") and the **full-file-read** rule (line 9 — "Read each changed/new file in full"). Expected outcome is **conformance** — the mentions gate already judges findings against the lifted tree, and the full-file-read rule already reaches past the diff; "no change" is the correct result, not a failure. Edit only if the audit finds a genuine gap (e.g. the tree gate stops short of the leaf where the planners now go to it), and if so make the minimal matching fix. Record the audit conclusion (conformant, or the gap fixed) as a short note on this task's line in the plan file — it rides the plan file, no separate report.

  (b) **Give the new annotations a reader (required edit).** Task 3 introduces the implementer's `DEVIATION:`/`BLOCKED:` plan-file annotations. The reviewer already reads the plan file for intent (Behavior step 1), but nothing tells it these lines are deliberate signals — so an uninformed reviewer could flag a `BLOCKED:` unchecked task as an incomplete-implementation defect, withhold `REVIEW_PASS`, and drive the implementer to invent the very decision it correctly escalated. Because the annotation protocol is born in this milestone and `reviewer.md` is edited here, giving it a reader is in-boundary. Add this block to the `## Behavior` section, immediately after item 1 (reading the plan for intent):

  ```markdown
  When the plan file carries implementer annotations, read them as deliberate signals, not defects:
  - `DEVIATION: <plan said / file showed / done>` — the implementer hit ground truth that disagreed with the plan and followed the file. Verify the change against the ground truth it cites; a correct deviation is conformance, not a finding.
  - `BLOCKED: <missing decision>` on a task whose checkbox is unchecked — a deliberate honest-incomplete state where the plan never made a needed decision, not an oversight. Surface the missing decision as the blocker to resolve; do not flag the unchecked box itself as a defect, and do not supply the missing decision yourself.
  ```

  Do not touch the Context Gates block, the Deferred-observations section, the REVIEW_PASS rules, or the `done`-output rule.

## Guards (carry into every task)
- **Prompts only** — no changes to `agents.py`, `main.py`, config, or `docs/`.
- Pass-signal contracts (`PLAN_REVIEW_PASS` / `REVIEW_PASS`) and the `done`-output rules stay untouched in every prompt.
- The width limiter is load-bearing: "to the leaf" must not turn into "read the whole tree."
