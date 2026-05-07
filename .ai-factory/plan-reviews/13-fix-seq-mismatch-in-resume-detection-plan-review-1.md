## Plan Review: Fix seq mismatch in resume detection

**Files Reviewed:** 5 (plan + `main.py`, `agents.py`, `roadmap.py`, `state.py`)
**Risk Level:** Low

### Context Gates
- `ARCHITECTURE.md` — not present (WARN, non-blocking)
- `RULES.md` — not present (WARN, non-blocking)
- `ROADMAP.md` — milestone exists and matches plan intent
- `skill-context/aif-review/SKILL.md` — not present (WARN, non-blocking)

### Problem Analysis

The plan correctly identifies the root cause: `_implement_loop` / `_refactor_loop` call `_next_number(plans_dir)` once per run to set the starting index for `enumerate`. If a previous run wrote a plan file (e.g., `49-slug.md`) and was interrupted, the next run gets `seq=50`. `_detect_milestone_step()` then checks `50-slug.md` (doesn't exist) and returns `("plan", 1)` — losing all `49-*` artifacts (plan-reviews, reviews, patches).

### Approach Validation

The slug-based scan approach is sound. Rather than changing `_next_number()` or the enumeration logic (which would have wider blast radius), the fix is scoped entirely to `_detect_milestone_step()` and its two callers. This is the right call — minimal surface area, no behavioral change when no prior artifacts exist.

Verified data flow:
1. `process_milestone` constructs initial `seq` / `plan_path` (lines 139-140) — unchanged.
2. Calls `_detect_milestone_step(... plan_path ...)` — function now scans by slug, returns canonical path.
3. Caller overrides `plan_path` and derives `seq` from it — all downstream uses (`plan_review_path`, `review_path`, agent calls, safety guard glob on line 204) automatically pick up the correct values.

Confirmed: no other callers of `_detect_milestone_step()` exist beyond `process_milestone` (line 146) and `process_refactor_milestone` (line 268). Both are covered by Tasks 3 and 4.

### Suggestions (non-blocking)

**1. Glob false-positive risk in slug matching.**
The glob `*-{slug}.md` can match files where the target slug is only a *suffix* of a longer slug. Example: milestone "Fix A" (slug `fix-a`) and milestone "Also fix A" (slug `also-fix-a`). The file `14-also-fix-a.md` matches the glob `*-fix-a.md` because `*` absorbs `14-also`.

In practice this is extremely unlikely given how distinct milestone titles are, but the implementer could add a one-line guard after extracting candidates: verify `candidate.stem.split("-", 1)[1] == slug`. This eliminates the false-positive class entirely at zero cost.

**2. Preserve string formatting when deriving canonical seq.**
The plan says "pick the match with the lowest numeric prefix" (implies `int()` comparison) but the seq must remain a string that matches the original filename prefix (e.g., `"09"` not `"9"`). The implementer should compare numerically but use the original string from the filename as the canonical seq — not `str(int(...))`.

### Critical Issues

None.

### Positive Notes

- Correct scoping: the fix lives entirely in `_detect_milestone_step()` + two callers. No changes to `_next_number()`, agent classes, or CLI entry points.
- The return-type change (`tuple[str, int]` → `tuple[str, int, Path]`) is a clean API evolution that makes the canonical path explicit rather than forcing callers to reconstruct it.
- Task 3's approach of deriving `seq` from the returned `plan_path` (rather than returning `seq` as a separate value) avoids a fourth return element and keeps the contract simple.
- Both `process_milestone` and `process_refactor_milestone` are covered symmetrically (Tasks 3 and 4).

PLAN_REVIEW_PASS
