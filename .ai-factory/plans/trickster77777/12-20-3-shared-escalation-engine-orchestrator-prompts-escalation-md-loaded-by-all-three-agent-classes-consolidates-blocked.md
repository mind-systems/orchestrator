# Plan: 20.3 — Shared escalation engine (`orchestrator/prompts/escalation.md`) loaded by all three agent classes; consolidates `BLOCKED:`

## Context
Give every agent role (planner, plan-reviewer, implementer, reviewer) the ability to reach the **escalation** run outcome by adding one shared prompt fragment concatenated into each agent's system prompt, and consolidate `BLOCKED:`'s scattered definitions into pointers at that engine. This is the prompt/wiring half only — no `agents.py` detection, resume, or notification logic (that is 20.4).

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: The engine file

- [x] **Task 1: Create `orchestrator/prompts/escalation.md`**
  Files: `orchestrator/prompts/escalation.md`
  New file, sibling of `planner.md`/`reviewer.md`/`implementer.md`/`test-planner.md`, loaded the same way via `_load_prompt("escalation")` (agents.py strips the `.md`). Write agent-facing prose in the terse, rule-list register of the existing three prompt files — no new vocabulary beyond what `docs/concepts/outcomes.md`'s `## Escalation` section and `docs/features/escalation.md` already name. The file states the contract the agent *writes to*; it does NOT describe `agents.py` internals, sidecar field names, or `resume.py` dispatch (those are implementation, not agent-facing contract). Cover exactly these four points:
  - **When to use it.** An agent recognizes that producing its own mandated output honestly would require deciding something outside its authority: a neighboring task's scope, the ratified spec above the current task, or an unresolved disagreement between two agents that no document settles.
  - **The marker.** Write the exact line `ESCALATION` on its own line, at the end of the artifact you are already writing (the plan file for the planner and the implementer; the plan-review or review file for the two reviewers) — mirroring `PLAN_REVIEW_PASS`/`REVIEW_PASS`'s existing exact-line convention, never mixed with either of those signals on the same file.
  - **The required content.** Immediately above the marker, a `## Escalation` section stating the missing decision and its options as a plain list. State the options; do not resolve them — picking one is exactly the authority you do not have.
  - **Effect.** The run stops immediately, before burning more of the iteration budget. This is not `BLOCKED:`'s old "leave this task's checkbox unchecked and let independent tasks continue" behavior — escalating halts the entire run, pending a human decision.
  Guard: no prohibitions, lectures, or new rules beyond stating this contract. Do NOT add a `Skill` tool reference — the engine is delivered via system-prompt concatenation, not a runtime tool.

### Phase 2: Prompt concatenation wiring

- [x] **Task 2: Fold the engine into each agent class's `system_prompt`** (depends on Task 1)
  Files: `orchestrator/orchestrator/agents.py`
  Add the escalation fragment to all three constructors, mirroring the existing `planner_prompt + reviewer_prompt` concatenation pattern (same `"\n\n---\n\n"` separator):
  - `PlannerReviewer.__init__` (`:325-327`): add `self.escalation_prompt = _load_prompt("escalation")` and set `self.system_prompt = self.planner_prompt + "\n\n---\n\n" + self.reviewer_prompt + "\n\n---\n\n" + self.escalation_prompt`.
  - `PlanReviewer.__init__` (`:418`): set `self.system_prompt = _load_prompt("reviewer") + "\n\n---\n\n" + _load_prompt("escalation")`.
  - `Implementer.__init__` (`:458`): set `self.system_prompt = _load_prompt("implementer") + "\n\n---\n\n" + _load_prompt("escalation")`.
  This gives all four roles the same engine text with zero duplication, including the `test-planner.md` variant — `PlannerReviewer.planner_prompt` is loaded by name (`planner_prompt_name`) and the concatenation is unconditional, independent of which planner prompt was requested. Do NOT touch `TestRunner` (no LLM session), and do NOT add any detection/parsing/`EscalationError` logic (that is 20.4).

### Phase 3: Consolidate `BLOCKED:` into pointers

- [x] **Task 3: Rewrite `implementer.md`'s `BLOCKED:` sites to point at the engine** (depends on Task 1)
  Files: `orchestrator/orchestrator/prompts/implementer.md`
  Three surgical edits, keeping every other line/section/rule untouched and preserving current bullet shape and rhythm:
  - `:116` (the "Escalate ambiguity" bullet under "Ground truth over the plan"): stop restating the `BLOCKED:` mechanism (the marker, the checkbox, "independent tasks continue" — that continuation behavior no longer holds and must not be restated even implicitly). Rewrite so a task blocked by a missing decision the plan never made escalates per the escalation engine (loaded above), keeping the same one-bullet shape/rhythm as its `DEVIATION:` sibling at `:115`.
  - `:118` ("Both annotations ride the plan file — no new files, no interactive prompts."): rewrite to the singular — "The annotation rides the plan file — no new files, no interactive prompts." — since only `DEVIATION:` remains a plan-file annotation this prompt defines; escalating writes the marker + `## Escalation` section into the artifact per the engine, not a bare plan-file annotation.
  - `:127` (Critical Rule 6): keep the `DEVIATION:` half exactly as-is; shrink the `BLOCKED:` half from restating "mark the task `BLOCKED:`... and leave it unchecked" to a pointer at the escalation engine.
  Guards: do NOT add a new entry to the numbered Critical Rules list; do NOT touch any other line/rule; after the edits the literal still-defined-annotation token `BLOCKED:` no longer appears in this file.

- [x] **Task 4: Shrink `reviewer.md`'s `BLOCKED:` bullet to a pointer** (depends on Task 1)
  Files: `orchestrator/orchestrator/prompts/reviewer.md`
  `:11` (the `BLOCKED:` bullet in the "read implementer annotations" list): shrink from restating `BLOCKED:`'s full semantics to a one-line pointer at the escalation engine, keeping the same bullet position and rhythm as its `DEVIATION:` sibling at `:10`. Guards: do NOT add a new entry to the Behavior list; do NOT touch any other line; after the edit the literal still-defined-annotation token `BLOCKED:` no longer appears in this file.

### Phase 4: Verify wiring

- [x] **Task 5: Confirm the engine loads and concatenates; suite stays green** (depends on Task 2, Task 3, Task 4)
  Files: (no changes — verification only)
  Confirm the spec's checks hold: `_load_prompt("escalation")` succeeds and is non-empty; the literal `ESCALATION` marker instruction appears in `PlannerReviewer`, `PlanReviewer`, and `Implementer` `system_prompt`s; `grep -n "BLOCKED" orchestrator/prompts/implementer.md orchestrator/prompts/reviewer.md` no longer shows `BLOCKED:` as a still-defined annotation (each site now names the engine); `grep -n "Both annotations" implementer.md` → no hits and `grep -n "The annotation rides" implementer.md` → one hit; `uv run pytest` still green (if any existing test asserts prompt-file content by string match, update it to expect the new concatenation — do NOT add new tests otherwise).
  Note: `planner.md` gets no textual edit — it never mentioned `BLOCKED:` and gains the capability purely through Task 2's concatenation.
