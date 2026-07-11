# prompts: one philosophy pass — load the written philosophy, roll it over every agent prompt

## Current state

The four agent prompts (`orchestrator/prompts/planner.md`, `test-planner.md`, `implementer.md`, `reviewer.md`) grew alongside the philosophy that the skills repo has since written down — and partially embody it already: both planners build the milestone's **context tree** ("Follow mentions", `planner.md:21-25`, `test-planner.md:18`), the reviewer judges findings against that tree and reads changed files in full. Two gaps remain: the planners' tree stops at **two hops** (a note referencing a note that names a code file is never followed to the end), and the implementer has **no discipline for a wrong or underspecified plan** (`grep "escalat\|contradict\|deviate" orchestrator/prompts/implementer.md` → zero) — the standing temptation is plausible invention, and silent deviation from a stale plan is invisible until review.

## Read first — the philosophy source (mandatory, before touching any prompt)

1. `~/projects/skills/docs/context-tree.md` — the tree model: input-to-leaf raising, the leaf is code, links as walked edges.
2. `~/projects/skills/docs/skill-composition-model.md` — what to pin vs. what to trust the executor with; the invention/interpretation trade-off ("Что специфицировать, а что доверить исполнителю").
3. `~/projects/skills/src/global/CLAUDE.md` § "Grounding claims" — the normative depth rule the prompts must mirror.

Then roll the philosophy over **all four prompts** — fix the two named gaps, and audit the other surfaces against the same source; where a prompt already conforms (the reviewer's tree gate is expected to), "no change" is the correct finding, not a failure.

## Change

- **Planners — mentions to the leaf** (`planner.md` + `test-planner.md`, identical text, the blocks stay a mirrored pair): recursion made explicit — every file the artifact names, then every file *those* name, depth along named edges **down to the leaf; the leaf is code**. The width limiter ("only links reachable from your milestone"; irrelevant branches dropped) and the unconditional `Governing spec:` read survive verbatim in meaning. A reference deliberately not opened is **attributed**, never paraphrased from memory.
- **Implementer — escalate, don't invent** (one rule block in the existing DO/DON'T register):
  - **Ground truth wins** — when the plan and the files on disk disagree, the file is the truth.
  - **Fix and flag, never silently deviate** — a stale path / wrong signature / mismatched value is implemented per ground truth and annotated on the task's line in the plan file: `DEVIATION: <plan said / file showed / done>`.
  - **Escalate ambiguity** — a task blocked by a missing decision gets `BLOCKED: <the missing decision>` on its line, checkbox stays unchecked, independent tasks continue. An unfinished honest plan beats a finished invented one.
- **Reviewer — audit only**: check its tree gate and full-file-read rules against the same philosophy; expected outcome is conformance (its mentions gate already judges findings against the tree). Fix only a real gap if the audit finds one.

## Files & types

- edit `orchestrator/prompts/planner.md`, `orchestrator/prompts/test-planner.md` (mirrored Follow-mentions block)
- edit `orchestrator/prompts/implementer.md` (one rule block + one Critical Rules line)
- audit `orchestrator/prompts/reviewer.md` (edit only on a found gap)

## Guards

- **Prompts only** — no Python, no config, no docs in this task.
- **Headless stays headless** — the implementer gains no interactivity and no new artifacts: both annotations ride the plan file (already the progress source of truth; the reviewer reads it); NO-tests / NO-reports / checkbox rules untouched.
- Block-level edits — plan format, commit rules, `done` output rules, pass-signal contracts untouched in every prompt.
- The width limiter is load-bearing: "to the leaf" must not become "read the whole tree".
- Annotations are for genuine contradictions and blocks, not commentary — the prompt says so.

## Verification

- `grep -n "to the leaf" orchestrator/prompts/planner.md orchestrator/prompts/test-planner.md` → both hit; the two blocks are identical (`diff` of the extracted blocks → empty).
- `grep -n "DEVIATION\|BLOCKED\|ground truth" orchestrator/prompts/implementer.md` → the block present.
- Live: plan a milestone whose spec note references a second note naming a code file → the plan's Context carries the code-level fact; run implement against a plan with one stale path and one missing decision → one `DEVIATION:`, one `BLOCKED:`, zero invented filler.
- The reviewer audit's finding (conformant or fixed) stated in the implementation report.
