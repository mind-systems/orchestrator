# Shared escalation engine, loaded by all three agent classes; consolidates `BLOCKED:`

**Date:** 2026-07-29
**Source:** conversation context (coordinator ruling: one shared engine, never duplicated per prompt; no added prohibitions/lectures; current prompt-body granularity preserved; `BLOCKED:` at `implementer.md:116`,`:127` and `reviewer.md:11` consolidates into it; `implementer.md:118` amendment pinned separately below)

## Problem today

`BLOCKED:` is defined independently in two places today, in different words: `orchestrator/prompts/implementer.md:116` ("a task blocked by a missing decision the plan never made gets `BLOCKED: <the missing decision>` on its line; its checkbox stays unchecked, and independent tasks continue"), restated at `:127` ("on a missing decision, mark the task `BLOCKED: <the missing decision>` and leave it unchecked rather than inventing"), and read (not written) at `reviewer.md:11` ("`BLOCKED: <missing decision>` on a task whose checkbox is unchecked — a deliberate honest-incomplete state..."). None of these three sites is authoritative over the others, and none gives the planner or plan-reviewer any equivalent capability — the incident (`.ai-factory/handoffs/09-...md`) shows a case where the missing decision reached outside the implementer's own task, into a neighboring task's spec and contract line, which this smeared, implementer-only mechanism has no way to name.

`implementer.md:118` — "Both annotations ride the plan file — no new files, no interactive prompts." — refers to `DEVIATION:` and `BLOCKED:` as a pair (`:115`, `:116`). Once `BLOCKED:` is consolidated into the new engine and stops being a plan-file annotation implementer.md defines locally, only `DEVIATION:` remains a plan-file annotation described by this prompt, and the plural "Both annotations" becomes false.

`PlannerReviewer.__init__` (`agents.py:317-331`), `PlanReviewer.__init__` (`agents.py:411-421`), and `Implementer.__init__` (`agents.py:451-462`) each build `self.system_prompt` from `_load_prompt(...)` calls with no shared fragment across all three — `PlannerReviewer` already concatenates two (`self.planner_prompt + "\n\n---\n\n" + self.reviewer_prompt`, `:325-327`), proving the concatenation mechanism exists, but there is no third piece any of them share.

## The change

**1. New file `orchestrator/prompts/escalation.md`** (sibling of `planner.md`/`reviewer.md`/`implementer.md`/`test-planner.md`, loaded the same way via `_load_prompt("escalation")`). Content (prose, matching the terse, rule-list register of the existing three prompt files — no new vocabulary beyond what `docs/concepts/outcomes.md`'s `## Escalation` section already names):

- **When to use it.** An agent recognizes that producing its own mandated output honestly would require deciding something outside its authority: a neighboring task's scope, the ratified spec above the current task, or an unresolved disagreement between two agents that no document settles.
- **The marker.** Write the exact line `ESCALATION` on its own line, at the end of the artifact you are already writing (the plan file for the planner and the implementer; the plan-review or review file for the two reviewers) — mirroring `PLAN_REVIEW_PASS`/`REVIEW_PASS`'s existing exact-line convention, never mixed with either of those signals on the same file.
- **The required content.** Immediately above the marker, a `## Escalation` section stating the missing decision and its options as a plain list. State the options; do not resolve them — picking one is exactly the authority you do not have.
- **Effect.** The run stops immediately, before burning any more of the iteration budget — this is not `BLOCKED:`'s old "leave this task's checkbox unchecked and let independent tasks continue" behavior; escalating halts the entire run, pending a human decision (mechanically wired in 20.4/20.5 — this file states the contract the agent writes to, not the harness code).

**2. `agents.py` concatenation.** Add `self.escalation_prompt = _load_prompt("escalation")` and fold it into each class's `system_prompt`:
- `PlannerReviewer.__init__` (`:325-327`): `self.system_prompt = self.planner_prompt + "\n\n---\n\n" + self.reviewer_prompt + "\n\n---\n\n" + self.escalation_prompt`.
- `PlanReviewer.__init__` (`:418`): `self.system_prompt = _load_prompt("reviewer") + "\n\n---\n\n" + _load_prompt("escalation")`.
- `Implementer.__init__` (`:458`): `self.system_prompt = _load_prompt("implementer") + "\n\n---\n\n" + _load_prompt("escalation")`.

This gives all four agent roles (planner, plan-reviewer, implementer, reviewer) the same engine text with zero duplication — including the `test-planner.md` variant, since `PlannerReviewer.planner_prompt` is loaded by name (`planner_prompt_name`) and the concatenation is unconditional in `__init__`, independent of which planner prompt was requested.

**3. `implementer.md:116`.** Rewrite the bullet from restating `BLOCKED:`'s mechanism to pointing at the engine, keeping the same one-bullet shape and rhythm as its `DEVIATION:` sibling at `:115`: state that a task blocked by a missing decision the plan never made escalates per the escalation engine (loaded above), rather than re-describing the marker, the checkbox, or "independent tasks continue" — that continuation behavior no longer holds (escalating halts the whole run, per 20.4/20.5), so it must not be restated here even implicitly.

**4. `implementer.md:127`** (Critical Rule 6). Same treatment — the rule currently restates both `DEVIATION:` and `BLOCKED:` mechanics in one line; keep the `DEVIATION:` half exactly as-is, and shrink the `BLOCKED:` half to a pointer at the engine instead of re-stating "mark the task `BLOCKED:`... and leave it unchecked".

**5. `implementer.md:118`.** Rewrite "Both annotations ride the plan file — no new files, no interactive prompts." to the singular — "The annotation rides the plan file — no new files, no interactive prompts." — since only `DEVIATION:` remains a plan-file annotation this prompt itself defines; escalating no longer rides the plan file as a bare annotation, it writes the marker + `## Escalation` section into the artifact per the engine (item 1 above).

**6. `reviewer.md:11`.** Shrink from restating `BLOCKED:`'s full semantics to a one-line pointer at the engine, keeping the same bullet position and rhythm as its `DEVIATION:` sibling at `:10`.

**7. `planner.md`.** No textual edit — it never mentioned `BLOCKED:`, and gains the escalation capability purely through the `agents.py` concatenation (item 2).

## Guards

- No prohibitions, lectures, or new rules added to any of the three prompt bodies beyond the pointer rewrites named above — the coordinator's ruling is explicit that current granularity is preserved. Do not expand `implementer.md`'s numbered Critical Rules list or `reviewer.md`'s Behavior list with a new entry; the escalation capability lives entirely in the new engine file, referenced, not restated.
- "Nothing else in the prompts changes" — do not touch any other line, section, or rule in `planner.md`, `reviewer.md`, or `implementer.md` beyond the five sites named (`implementer.md:116,118,127`; `reviewer.md:11`).
- No detection/parsing logic in this task — `agents.py`'s `_has_signal`, the `EscalationError` class, and the four per-method checks are 20.4's scope. This task only makes the marker/grammar known to the model and wires the prompt concatenation.
- The engine file states the contract in agent-facing prose (what to write, when, why) — it does not describe `agents.py` internals, sidecar field names, or `resume.py` dispatch; those are implementation, not agent-facing contract.

## Verify

- `_load_prompt("escalation")` succeeds (the file exists, non-empty).
- `PlannerReviewer(...).system_prompt`, `PlanReviewer(...).system_prompt`, and `Implementer(...).system_prompt` each contain the escalation engine's text (spot-check: the literal string `ESCALATION` marker instruction appears in all three).
- `grep -n "BLOCKED" orchestrator/prompts/implementer.md orchestrator/prompts/reviewer.md` — the literal token `BLOCKED:` (as a still-defined annotation form) no longer appears; each site instead names the escalation engine.
- `grep -n "Both annotations" orchestrator/prompts/implementer.md` → no hits; `grep -n "The annotation rides" orchestrator/prompts/implementer.md` → one hit.
- `uv run pytest` still green (no test currently asserts prompt-file content by string match beyond what may already exist — if one does, update it to expect the new concatenation).

## What NOT to do

- Do not add `Skill` to any agent's `allowed_tools`/`--allowedTools` list — this engine is delivered via system-prompt concatenation (`_load_prompt`), not a runtime tool call; there is no `Skill` tool in this harness's vocabulary at all (that concept belongs to the Claude Code skills family, not this Python CLI harness).
- Do not touch `test-planner.md` — it inherits the engine automatically via `PlannerReviewer`'s constructor regardless of `planner_prompt_name`.
- Do not touch `TestRunner` — it has no LLM session and cannot escalate.
- Do not write the `EscalationError` class or any `agents.py` detection logic — that is 20.4.
