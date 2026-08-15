# A plan's tasks are named by subject, not numbered

**Date:** 2026-08-15
**Source:** this session's investigation of why a task written after Phase 19 still emitted a plan coordinate

## Problem today

Three prompt sites pin or police the plan's numbered-task shape:

- `planner.md:94-108`'s template spans numbered phase headers — `### Phase 1: <name>` at `:94`, `### Phase 2: <name>` at `:104` — alongside three numbered task lines (`:96`, `:100`, `:106`):
  ```
  - [ ] **Task 1: <subject>**
  - [ ] **Task 2: <subject>** (depends on Task 1)
  ```
- `test-planner.md:94-107`'s template spans a phase header — `### Phase 1: <group name — e.g. "TradeAggregator — core behavior">` at `:94` — alongside two numbered task lines (`:96`, `:103`): `- [ ] **Task 1: <describe block subject>**`
- `implementer.md`'s three sites: the Step 2.3 checkbox example (`:55-61`), whose before/after lines (`:57`, `:60`) read `- [ ] Task 1: Create user model` / `- [x] Task 1: Create user model`; the ban list at `:108` (no `Phase N`, no `Task N`/`task N.M`, no note number, no `ROADMAP`/`Plan` reference, no `.ai-factory/` path); and rule 7 at `:128`, which already names the mechanism — "the plan's `**Task N:**` headers are scaffolding for your own walk through the work, never content to transcribe" — and still only asks the implementer not to transcribe them, rather than removing the number the template hands it in the first place.

The rule was fully in force at `9006125` (Phase 19 — both the widened ban and rule 7 landed there). `c35291e` (`20.4`), the first implement task to run after it, wrote `# Task 5: escalated is always valid — a terminal, unindexed step` into `tests/test_main.py` two days later — the label the prompt now offers did not displace the number on its first real outing.

## The change

**1. `planner.md`'s template drops every number — task and phase alike.** A task's header is its subject alone; a dependency names the subject it depends on, not a number. The same diagnosis applies to the phase number: the plan is the only structure the implementer is handed, `Phase N` is one of the shapes `implementer.md`'s ban already forbids, and the template must not keep supplying what the ban forbids — a phase's header is its name alone, symmetric with a task's:

```
### <phase name>

- [ ] **<subject A>**
  Files: `path/to/file.ext`, `path/to/other.ext`
  <What to do, specifically. Reference existing patterns found in codebase.>

- [ ] **<subject B>** (depends on <subject A>)
  Files: `path/to/file.ext`
  <What to do.>

### <another phase name>

- [ ] **<subject C>** (depends on <subject B>)
  Files: `path/to/file.ext`
  <What to do.>
```

A dependency clause repeats the depended-on task's subject **verbatim** — the number was reference-safe by construction, the subject is reference-safe only if never paraphrased — and subjects within one plan are distinct.

**2. `test-planner.md`'s template drops the number the same way — phase and task alike.** Its phase header at `:94` drops its number too (`### <group name — e.g. "TradeAggregator — core behavior">`). Its two tasks carry no dependency clause today, so only the header changes:

```
- [ ] **<describe block subject>**
  Files: `<target spec file>`
  Test cases:
  - `should <expected behavior> when <condition>`
  - `should <expected behavior> when <condition>`
  - `should throw <error> when <condition>`

- [ ] **<describe block subject>**
  Files: `<target spec file>`
  Test cases:
  - `should <expected behavior> when <condition>`
  - `should <expected behavior> when <condition>`
```

**3. `implementer.md`'s ban line and rule 7 lead with the plan's standing, not with a shape list.** A plan is instruction — the same status as this prompt — and it stops existing once the task closes; what is built from an instruction does not cite it. The concrete shapes stay, but only as examples of what that rule already rules out, never as the rule itself:

- Ban line (`:108`): "Cite the plan layer in any durable text this repository carries outside `.ai-factory/` — a code or test comment, a docstring, a module header, or whatever other construct holds it. A plan is instruction — the same status as this prompt — and it stops existing once the task closes; what is built from an instruction does not cite it. That rules out `Phase N`, `Task N`/`task N.M`, a note number, a `ROADMAP`/`Plan` reference, and an `.ai-factory/` path, among any other form the same citation takes — explain the behavior self-contained, or link a file under `docs/` (the only reference target allowed in code)."
- Rule 7 (`:128`): "**A plan is instruction, not a source — nothing built from it cites it.** A plan is the same status as this prompt: read to guide the work, gone once the task closes. No durable text this repository carries outside `.ai-factory/` — a comment, a docstring, a module header, or whatever other construct holds it — carries a plan coordinate: `Phase N`, `Task N`/`task N.M`, a note number, a `ROADMAP`/`Plan` reference, an `.ai-factory/` path, or any other shape the same citation takes. A test file's sections and docstrings are named by the behavior under test; a plan's task headers are scaffolding for your own walk through the work, never content to transcribe. Explain the behavior self-contained, or link a file under `docs/`."

The order matters because an enumerated shape list has already lost twice to a construct it did not anticipate: a module docstring (`.ai-factory/handoffs/08-plan-layer-citations-recur-in-docstrings.md`) and a `.proto` interface-definition comment (`.ai-factory/handoffs/09-implementer-rewrote-the-spec-and-roadmap-tiers.md` § 5) — both technically outside "code/test comments," both real leaks a literal reader could excuse. Leading with the principle means a fourth construct the list never named still falls inside the rule; the concrete shapes are its illustration, not its boundary. Both lists — the shapes a citation takes and the constructs that can hold one — are examples in the same sense; the principle draws the boundary, neither enumeration does.

**4. `implementer.md`'s Step 2.3 checkbox example loses its label's number.** The before/after example (`:55-61`) illustrates the `- [ ]` → `- [x]` toggle mechanic using a numbered task label; left unchanged, it would go stale the moment the planner stops writing `Task 1:` headers, and it is a residual instance of the exact shape this task removes, sitting inside the prompt that argues against it:

```
# Before
- [ ] Create user model

# After
- [x] Create user model
```

Only the label changes — the surrounding Step 2.3 text and the `- [ ]` → `- [x]` toggle mechanic are untouched.

## Guards

- Existing `# Task N:` headings in `tests/` are not swept; Phase 19 holds them as the cross-repo ask's evidence, and this task adds none of its own.
- No gate, check, or scan is added to `reviewer.md` or anywhere downstream — the point is that the coordinate stops being handed to the agent in the first place; a downstream check would only police what we ourselves keep supplying.
- No code changes. Nothing parses a plan's task structure: `roadmap.py:93,110` are the two checkbox rewrites, and they act on the roadmap, never on a plan; no other code anywhere in `orchestrator/` reads a plan's task headers.
- The plan's walk order is its list order and stays exactly as it is — only the label on each item changes.

## Tests

None, and deliberately so: a prompt is not a surface `test-philosophy`'s discriminator names — there is no code path whose wrong output would pass unnoticed by a compiler, a runtime, or an HTTP layer. What this task governs is an agent's behavior, observable only in what the next plan and the next test file look like, not in an assertion. Do not let an implementer invent one.

## Verify

- `grep -nE "(Task|Phase) [0-9]" orchestrator/prompts/planner.md orchestrator/prompts/test-planner.md orchestrator/prompts/implementer.md` returns nothing. (Grounded: the ban line at `:108` and rule 7 at `:128` keep `Task N`/`task N.M`/`Phase N` as illustration shapes, and the letter `N` does not match the digit class — today's only digit matches are the template lines and the `:57`/`:60` example, all of which this task removes.)
- `implementer.md`'s two rule sites state the plan's standing before naming any shape — read them, don't grep for it.
- Observational, not a test: the next plan the orchestrator writes carries no numbered task header, and the sections it writes into a test file are named by the behavior under test, not by a plan coordinate.

## What NOT to do

- Do not sweep the existing `# Task N:` headings in `tests/` — Phase 19 holds them deliberately.
- Do not add a downstream check, gate, or scan.
- Do not touch `reviewer.md`.
- Do not change the plan's ordering, its checkbox format, or its `Files:`/dependency structure beyond dropping the task and phase numbers.
- Touch `orchestrator/prompts/planner.md`, `orchestrator/prompts/test-planner.md`, and `orchestrator/prompts/implementer.md` only.
