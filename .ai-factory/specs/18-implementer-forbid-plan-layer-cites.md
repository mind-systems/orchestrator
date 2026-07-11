# implementer: forbid plan-layer citations in durable code and tests

## Current state

`orchestrator/prompts/implementer.md` carries no rule stopping the implementer from writing a plan-layer label into durable code or tests. The implementer is handed a plan file titled `Phase N.M` and a spec note numbered `NN`, and — with no "annotate" instruction anywhere — narrates its current task into a comment: `// Phase 9.3.1`, `// note 39`, an `.ai-factory/specs/…` path. The leak is **emergent** (it happens from narration alone, not from any instruction), and it is worse than a dead link: `roadmap-prune` reuses freed phase/note numbers, so a stamped citation later resolves to an *unrelated live phase* — a confident false pointer, not an honest dangling one.

The prompt actively trains the reflex it must now fence: the "Ground truth over the plan" block (`implementer.md:109-117`) tells the implementer to write `DEVIATION:` / `BLOCKED:` annotations onto the plan-file line — correct, those ride *inside* `.ai-factory/` — but the same plan-referencing narration mode bleeds into code comments.

The global `~/.claude/CLAUDE.md` does reach this agent (it is a symlink to `~/projects/skills/active/CLAUDE.md`, and user-scoped memory loads regardless of the `--system-prompt` replace flag at `agents.py:135` and regardless of the target-project `cwd`). Reachability is not salience against an emergent leak — the enforcing surface is this one agent's own system prompt, which is where the writing happens.

## Change

Add a short **positive** prohibition to `implementer.md` (deletion is impossible — nothing instructs the annotation; only a positive rule can fence emergent narration). Two insertions, matching the file's existing echo idiom where a hard mandate appears in both the `DON'T` list and `Critical Rules` (as `NEVER write tests` already does):

- One bullet in **Execution Rules → DON'T**.
- One numbered line in **Critical Rules**.

The rule: *a code or test comment never carries a `Phase N`, a note number, a `ROADMAP`/`Plan` reference, or any `.ai-factory/` path; it either explains the behaviour self-contained, or links a file under `docs/` that owns it. `docs/` is the only reference target allowed in code.*

## Files & types

- edit `orchestrator/prompts/implementer.md` only (one DON'T bullet + one Critical Rules line).

## Guards

- **Prompts only** — no Python, no config, no docs. **Do not touch memory** (`~/.claude/CLAUDE.md` stays as-is — explicit scope decision; the rule is single-homed there on the skills side, this is its operational projection into the writer).
- **Directional boundary** — the rule forbids *durable code/tests* citing *into* `.ai-factory/`; the plan layer citing itself stays legal. Leave the `DEVIATION:`/`BLOCKED:` plan-file annotations, the checkbox updates, the `Spec:`-tag/plan reads — every plan-layer-internal reference — untouched.
- **`docs/` is the only allowed reference target** from code; no provenance-via-`git`/`ARCHITECTURE.md` clause in the wording (deliberately dropped — superfluous).
- **Sibling prompts untouched** — `planner.md` / `test-planner.md` / `reviewer.md` get no edit; plans live inside `.ai-factory/` and cite the plan layer legally.
- Keep it short and operational — not a restatement of the skills-side essay. No new interactivity, no new artifacts; NO-tests / NO-reports / checkbox / pass-signal contracts untouched.

## Verification

- `grep -ni "\.ai-factory\|Phase N\|docs/" orchestrator/prompts/implementer.md` → the DON'T bullet and the Critical Rules line both present; no other block changed (`git diff` shows only the two additions).
- Live: run implement on any milestone whose plan is titled `Phase N.M`, then grep the resulting diff over `*.py` and tests for `Phase `, `note `, `ROADMAP`, `Plan `, `.ai-factory` → zero hits in comments; any comment present either explains behaviour or points at a `docs/` file.
- Plan format, the `DEVIATION:`/`BLOCKED:` block, `done`-output, and pass-signal contracts read identically to before.
