# Plan Review: Fix stderr pipe deadlock in `_run_claude`

**Plan reviewed:** `35-fix-stderr-pipe-deadlock-in-run-claude.md`
**Target:** `orchestrator/agents.py` → `_run_claude`
**Risk Level:** 🟢 Low

## Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): WARN — no boundary/dependency concern. The change is internal to `_run_claude`'s subprocess plumbing and touches no module boundaries.
- **Rules** (`.ai-factory/RULES.md`): WARN — file absent; no convention checks to apply.
- **Roadmap** (`.ai-factory/ROADMAP.md` present): WARN — this is a `fix` task; no explicit roadmap milestone linkage was found in the plan. Non-blocking.

## Diagnosis Validity
The deadlock the plan targets is real and correctly characterized. The code consumes stdout line-by-line in `for line in proc.stdout:` (line 149) but only reads `proc.stderr` **after** `proc.wait()` (line 171). If the child fills its stderr pipe buffer (~64KB) it blocks on writing stderr, stops producing stdout, and the stdout reader loop blocks forever — classic pipe deadlock. Merging stderr into stdout via `stderr=subprocess.STDOUT` eliminates the second pipe entirely, so the single stdout reader drains everything. Correct fix.

## Accuracy Check (verified against source)
- **Task 1** — Popen at lines 135–142 with `stderr=subprocess.PIPE` (line 138). Matches. The cited reference pattern at line 421 (`stderr=subprocess.STDOUT`) is real and is the right precedent.
- **Task 2** — `stderr = proc.stderr.read()...` is exactly at line 171. After Task 1, `proc.stderr` is `None`, so the read is dead and must be removed. Correct.
- **Task 3** — The two `RuntimeError` blocks reference the `stderr` local at lines 208 and 215. Confirmed these are the only other uses. `grep` shows all four occurrences (138, 171, 208, 215) are accounted for; line 421 is the unrelated TestRunner reference. No dangling `stderr` reference will remain.

## Observations (non-blocking)
- After merging, the stdout-parsing loop and the "find final result event" scan will now also see non-JSON stderr lines. Both paths already swallow `json.JSONDecodeError`, so interleaved stderr text is harmless. No change needed.
- The empty-stdout guard `if not lines:` (line 212) now becomes "no output on either stream," since stderr lines also land in `lines`. This is strictly an improvement: a child that emits only stderr no longer trips this branch, and the merged stderr is already visible in the `stdout`/`lines` content of the exit-code error message. The plan's instruction to keep "a clear message that stdout was empty" is fine — consider phrasing it as "no output" for accuracy, but this is cosmetic.
- The exit-code RuntimeError still includes `stdout` (joined `lines`), which now carries the merged stderr — so diagnostic information is preserved, not lost. Good.

## Conclusion
The plan is well-scoped, the line references are accurate, the dependency ordering (Task 1 → 2 → 3) is correct, and it follows an existing in-repo pattern. No missing steps, no wrong assumptions, no migrations needed.

PLAN_REVIEW_PASS
