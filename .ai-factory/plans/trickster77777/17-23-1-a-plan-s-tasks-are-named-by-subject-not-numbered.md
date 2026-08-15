# Plan: 23.1 — A plan's tasks are named by subject, not numbered

## Context
Remove the plan coordinate at its source: `planner.md` and `test-planner.md` stop handing the implementer a numbered task list under numbered phase headers, and `implementer.md` follows — its checkbox example loses its `Task 1:` label, and its two rule sites lead with the plan's standing (instruction, not a source) instead of an enumerated shape list. Prompt text only; no code, no tests, no downstream check.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: The two templates drop every number

- [x] **Task 1: `planner.md`'s plan template drops task and phase numbers**
  Files: `orchestrator/prompts/planner.md`
  Replace the template body at `:94-108` (inside the ` ```markdown ` block under `## Tasks`) so a task's header is its subject alone and a phase's header is its name alone. Target text, verbatim:
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
  Nothing else in the file changes: the `# Plan:`/`## Context`/`## Settings`/`## Tasks` headings, the `- [ ]` checkbox format, the `Files:` line, the two-space continuation indent, the fence, `## Task Description Requirements`, and the eight Important Rules stay exactly as they are. The dependency clause keeps its `(depends on …)` wording and now repeats the depended-on task's subject verbatim — per the spec, a subject is reference-safe only if never paraphrased, and subjects within one plan are distinct.

- [x] **Task 2: `test-planner.md`'s plan template drops task and phase numbers**
  Files: `orchestrator/prompts/test-planner.md`
  Same change at `:94-107`. The phase header at `:94` loses its number, keeping its example: `### <group name — e.g. "TradeAggregator — core behavior">`. The two task headers at `:96` and `:103` become `- [ ] **<describe block subject>**`. These two tasks carry no dependency clause today and gain none. Target text, verbatim:
  ```
  ### <group name — e.g. "TradeAggregator — core behavior">

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
  Everything above (`## Test Command`, `## Target Spec File`) and below (`**Task grouping rules:**`, `**Test case rules:**`, `## Important Rules`) is untouched — including the grouping rules' use of the word "task", which is the reserved word at plan altitude, not a coordinate.

### Phase 2: `implementer.md` follows

- [x] **Task 3: Step 2.3's checkbox example loses its label's number** (independent of Task 1)
  Files: `orchestrator/prompts/implementer.md`
  In the Step 2.3 example (`:55-61`), change the before/after lines only:
  ```
  # Before
  - [ ] Create user model

  # After
  - [x] Create user model
  ```
  The `# Before` / `# After` markers, the fence, the surrounding Step 2.3 prose, and the `- [ ]` → `- [x]` toggle mechanic (`**This is MANDATORY**` bullets) stay exactly as they are.

- [x] **Task 4: The ban line and rule 7 lead with the plan's standing, not with a shape list** (depends on Task 3)
  Files: `orchestrator/prompts/implementer.md`
  Two rule sites are rewritten so the principle draws the boundary and the concrete shapes are illustration only — an enumerated list has already lost twice to a construct it did not anticipate (a module docstring, a `.proto` comment; see the handoffs the spec names). Both keep their position: the first stays the last bullet of the `### DON'T:` list, the second stays item 7 of `## Critical Rules`.

  Ban line (`:108`) becomes, verbatim:
  ```
  - Cite the plan layer in any durable text this repository carries outside `.ai-factory/` — a code or test comment, a docstring, a module header, or whatever other construct holds it. A plan is instruction — the same status as this prompt — and it stops existing once the task closes; what is built from an instruction does not cite it. That rules out `Phase N`, `Task N`/`task N.M`, a note number, a `ROADMAP`/`Plan` reference, and an `.ai-factory/` path, among any other form the same citation takes — explain the behavior self-contained, or link a file under `docs/` (the only reference target allowed in code).
  ```

  Rule 7 (`:128`) becomes, verbatim:
  ```
  7. **A plan is instruction, not a source — nothing built from it cites it.** A plan is the same status as this prompt: read to guide the work, gone once the task closes. No durable text this repository carries outside `.ai-factory/` — a comment, a docstring, a module header, or whatever other construct holds it — carries a plan coordinate: `Phase N`, `Task N`/`task N.M`, a note number, a `ROADMAP`/`Plan` reference, an `.ai-factory/` path, or any other shape the same citation takes. A test file's sections and docstrings are named by the behavior under test; a plan's task headers are scaffolding for your own walk through the work, never content to transcribe. Explain the behavior self-contained, or link a file under `docs/`.
  ```
  Note that rule 7's old wording cited the template it is losing (`the plan's **Task N:** headers`); the new wording says "a plan's task headers" instead. Rules 1–6 and 8 keep their numbers and text. After this task, `grep -nE "(Task|Phase) [0-9]" orchestrator/prompts/planner.md orchestrator/prompts/test-planner.md orchestrator/prompts/implementer.md` returns nothing — `Task N`/`Phase N` survive as illustration shapes and the letter `N` is not a digit.

## Guards for every task above
- Touch `orchestrator/prompts/planner.md`, `orchestrator/prompts/test-planner.md`, and `orchestrator/prompts/implementer.md` only — no code, no docs, no `reviewer.md`.
- No tests. A prompt is not a silent-failure surface; the spec forbids inventing one.
- Do not sweep the existing `# Task N:` headings in `tests/` — Phase 19 holds them deliberately as the cross-repo ask's evidence.
- Do not add any downstream check, gate, or scan.
- Do not change a plan's ordering, its checkbox format, or its `Files:`/dependency structure beyond dropping the task and phase numbers.
