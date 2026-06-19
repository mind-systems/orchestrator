## Plan Review: Dynamic roadmap re-scan loop

**Files Reviewed:** plan + `orchestrator/main.py`, `orchestrator/roadmap.py`, `orchestrator/state.py`, ROADMAP item 29
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture (`.ai-factory/ARCHITECTURE.md`):** PASS. Change is confined to `main.py`; dependency direction `main.py → agents.py → roadmap.py` is preserved (`_run_dynamic_loop` consumes `parse_roadmap` / `mark_done` from `roadmap.py`, no new inward deps). Layered pattern intact.
- **Rules (`.ai-factory/RULES.md`):** WARN — file absent; no explicit convention violations detectable.
- **Roadmap (`.ai-factory/ROADMAP.md`):** PASS. Plan maps directly to milestone 29 ("Dynamic roadmap re-scan loop"). Its prerequisite — note 14 "Relocate roadmap line by title at mark time" — is already `[x]` done; `_find_milestone_line` (roadmap.py:73) provides the robust, line-shift-tolerant marking the termination argument relies on.
- **Skill-context (`aif-review/SKILL.md`):** absent — no project-specific overrides to apply.

### Verified Against Codebase
- `state.stop_requested` exists (`state.py`) — `while not state.stop_requested:` is valid.
- `PipelineStopError` already imported in `main.py` (line 13) — guard `raise` needs no new import.
- `parse_roadmap` returns `ParseResult(milestones, breakpoint_hit, milestones_after_breakpoint)`; `Milestone` exposes `.title`, `.description`, `.done`, `.slug`, `.section`, `.line_number` — all fields the plan references are real.
- `process_milestone` / `process_test_milestone` return `str | None` (session id) and accept `phase_session_id=` — the `process_fn` lambda contract holds, and `phase_session_id = process_fn(...)` is type-correct.
- Re-computing `i = _next_number(plans_dir)` per iteration is sound: a completed milestone writes `NN-slug.md`, so the next call returns `NN+1`. The resume note is correct — `_detect_milestone_step` (and the test variant) re-resolves canonical seq via `glob("*-{slug}.md")`, so a divergent `_next_number` still reuses the existing lower-seq plan file.
- `---STOP---` handling: `parse_roadmap` already drops post-marker milestones, so re-parsing each iteration keeps them out without extra work.
- Section / phase-session reset logic mirrors the existing loops (lines 711–715) and remains equivalent under re-parse, since the sequence of `pending[0]` values across iterations matches the old fixed-list order (each processed milestone flips its checkbox and drops out).

### Critical Issues
None. The plan is implementable as written and the termination argument (checkbox-flip + `last_signature` backstop) is sound given note 14 is complete.

### Non-blocking Notes (WARN)
1. **Test-mode startup wording regresses.** The plan instructs `_run_dynamic_loop` to mirror `_implement_loop`'s generic wording (lines 689–697): `"All milestones are done!"` / `"Found N pending milestones …"`. The current `_test_loop` (lines 647–655) prints the *test-specific* variant: `"All test milestones are done!"` / `"Found N pending test milestones …"`. Routing both loops through the shared helper silently drops "test" from those messages. Cosmetic only, but if parity matters, pass a noun label (e.g. `milestone_noun="milestone"`/`"test milestone"`) into `_run_dynamic_loop` and interpolate it into the summary strings.

2. **`last_signature` false-positive on duplicate-titled milestones.** The guard compares `(title, description)` only against the immediately preceding selection. Two consecutive pending milestones with identical title+description would trip the guard on the second one and raise `PipelineStopError`, even though the first was legitimately completed. This is largely pre-existing risk — duplicate titles already collide on `slug` → same `plan_path` — so it's an edge case, not a new defect. Worth a one-line comment near the guard documenting that duplicate-titled milestones are unsupported, so a future reader doesn't mistake the stop for a real bug.

3. **`_run_loop` (line 70) becomes dead code.** The plan correctly leaves it in place and notes it "may have other callers." Confirmed: there are no other callers in the source tree (only the function's own definition). Not blocking — leaving it is a safe, reversible choice — but a follow-up could remove it.

### Positive Notes
- Correctly identifies that termination hinges on note 14's robust marking and confirms the dependency is satisfied.
- Precise about resume safety (slug-glob canonicalization) and `---STOP---` behavior — both verified accurate.
- Thin-wrapper decomposition keeps `process_*` signatures untouched, minimizing blast radius and honoring the layered architecture.
- Guard ordering (signature check → `_next_number` → `_check_usage_limits` → process) is reasonable and avoids burning a usage check on a milestone it's about to refuse.

PLAN_REVIEW_PASS
