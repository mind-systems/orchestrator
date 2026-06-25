## Plan Review: `parse_roadmap` + roadmap helpers unit tests

**Plan:** `43-parse-roadmap-roadmap-helpers-unit-tests.md`
**Target source:** `orchestrator/roadmap.py`
**Target spec:** `tests/test_roadmap.py`
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture** (`ARCHITECTURE.md` present): No boundary/dependency concern. Adding a unit-test module under `tests/` aligns with the existing test layout (`test_main.py`, `test_agents.py`). WARN: none.
- **Rules** (`RULES.md` absent): Gate skipped (optional file). WARN: missing optional file.
- **Roadmap** (`ROADMAP.md` present): This is test-authoring work (test mode milestone), not `feat`/`fix`/`perf`, so milestone linkage is N/A. No action.

### Correctness Verification (plan claims vs. code)
All concrete claims in the plan were verified against `orchestrator/roadmap.py`:

- Line references are accurate: `roadmap.py:9` is `CHECKBOX_RE` with the `[—–-]` dash class; `roadmap.py:50` is the `## ` / `### ` heading match; `roadmap.py:97` is the `{hours}h {mins}m {secs}s` formatting.
- Imports `parse_roadmap, Milestone, _find_milestone_line, mark_done, mark_skipped` all exist and are public/importable.
- Slug cases hold: `"Config file — replace env vars"` → `config-file-replace-env-vars` (em dash + spaces collapse via `[^a-z0-9]+` → `-`, then `strip("-")`); `"OAuth2 setup"` → `oauth2-setup` (digits preserved); leading/trailing hyphen stripping is the `.strip("-")` on line 25.
- Elapsed formatting: `125` → `2m 5s` (hours falsy → no hours segment); `3725` → `1h 2m 5s`. Matches `divmod` logic on lines 95–97.
- Breakpoint logic: `breakpoint_hit = marker_found and milestones_after_breakpoint > 0` (line 69) correctly yields `False` for a trailing `---STOP---` with nothing after it (case 3) and `False`/`0` when no marker is present.
- Case 13 (stale `line_number=0`, title on line 3): `mark_done` calls `_find_milestone_line` first (line 89) and only falls back to `milestone.line_number` when it returns `None`, so it correctly resolves to line 3. Verified.
- `mark_skipped` replaces `- [ ]` with `- [x] ⚠️ SKIPPED (already implemented)` via a count-limited `replace(..., 1)`, preserving the trailing `— description`. Matches case 12.
- The note that `## ` and `### ` both need explicit prefix checks is correct: `"### Foo".startswith("## ")` is `False`, so line 50's separate `### ` clause is genuinely required — the plan's reasoning is sound.

Test style guidance (module-level `def test_*`, one-line docstrings, `tmp_path`) matches `tests/test_main.py`, and the test command `uv run pytest tests/test_roadmap.py` is consistent with the existing test directory.

### Minor Suggestions (non-blocking)
- **Uncovered branch:** The pure fallback path in `mark_done`/`mark_skipped` — `_find_milestone_line` returns `None`, so `idx = milestone.line_number` is used (lines 90–91, 107–108) — is not explicitly exercised. Case 13 covers the find-*succeeds* path. Consider one case where the title is absent/already-checked but `line_number` still points at the right line, to lock down the fallback. Optional.
- **Regex requires a description:** `CHECKBOX_RE` mandates a non-empty description after the dash (`(.+)$`). The case-5 "no title checkbox pattern" test should ideally also cover a `- [ ] **Title**` line with *no* dash/description, since that is a realistic near-miss that the regex rejects. Optional enhancement to the existing negative case.

### Positive Notes
- Test cases are specified as concrete, behavior-named expectations with exact inputs/outputs — directly implementable without guesswork.
- Plan correctly flags the Unicode-dash subtlety (use real `—`/`–` characters in fixtures) which is an easy trap.
- Coverage spans parsing, slug generation, line lookup, and file mutation including the stale-`line_number` recovery path — the behaviors that actually drive the orchestrator loop.

The plan is solid, accurately models the target code, and is ready for implementation.

PLAN_REVIEW_PASS
