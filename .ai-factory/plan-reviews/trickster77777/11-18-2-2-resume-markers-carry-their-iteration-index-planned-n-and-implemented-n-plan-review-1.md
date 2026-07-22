## Plan Review Summary

**Plan:** 18.2.2 — Resume markers carry their iteration index (`planned:N` / `implemented:N`)
**Files Reviewed:** plan + `orchestrator/resume.py`, `orchestrator/main.py`, `tests/test_main.py`, governing spec `32-resume-carries-verify-iteration.md`, roadmap line 81, Herald sidecar
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): OK. The change is confined to `main.py` + `resume.py` (the resume/file-protocol machinery) plus one test fixture and a one-time external sidecar. No module boundary is crossed; the marker-grammar change is fully internal to the resume state machine. No WARN.
- **Rules** (`.ai-factory/RULES.md`): absent — optional gate skipped.
- **Roadmap** (`.ai-factory/roadmaps/trickster77777.md:81`): OK. The `[ ]` contract line matches the plan and its `Spec:` links to `32-resume-carries-verify-iteration.md`. Notably the contract line itself specifies `f"planned:{n}"` "(incl. a new `planned:{attempt+1}` after the re-plan)" — i.e. it already calls for the *round number*, not a literal `1`. This confirms the plan's DEVIATION on Task 3.1 (below) is contract-conformant, not a drift.

### Verification Against Ground Truth

Each edit was checked against the actual code:

- **Task 1** (`_validate_sidecar_step`, `resume.py:31`, `:48-55`): The bare tuple `("planned", "implemented")` at line 31-32 exists exactly as described; removing it is safe because bare markers are no longer written (verified: all five `_write_session(..., "step", ...)` sites at `main.py:277,291,301,329,348` are either indexed or become indexed by this task). The proposed `planned:`/`implemented:` branch mirrors the `fail_prefix` parse-guard shape, correctly omits the artifact-existence stat (structural validity), and its prefixes are disjoint from `plan_review_failed:` / `review_failed:` / `test_run_failed:`, so placement before the `plan_review_failed:` check is order-safe. Matches the green expectations of the 18.2.1 tests at `tests/test_main.py:66-87`.

- **Task 2** (`_detect_step`, `resume.py:122-123`, `:129-130`): Replacing the two `==` branches with prefix branches is correct. Prefix order is safe (`"planned:"` never prefixes `"plan_review_failed:"`; `"implemented:"` never prefixes the fail tags). Both thin wrappers (`_detect_task_step`, `_detect_test_task_step`) inherit the sole dispatch site unchanged, so `implemented:N → (test_run, N)` in test mode is covered — matches `tests/test_main.py:680-684`.

- **Task 3.1** (`main.py:277`, `f"planned:{counter}"`): The **DEVIATION** from the spec sketch's literal `planned:1` is verified correct and is the stronger reading. Trace: resume from a crash *inside* the re-plan leaves `plan_review_failed:N → ("plan", N+1)`, which re-enters the plan block at `main.py:263` with `counter = N+1` and re-hits line 277. A literal `planned:1` there would make a subsequent crash resume as `("plan_review", 1)` — re-reviewing attempt 1 against the attempt-(N+1) plan, overwriting `plan-review-1.md` and resetting the plan-review budget: exactly the bug class this task removes. `f"planned:{counter}"` is byte-identical to `planned:1` when `counter == 1` and correct on resume. It satisfies the governing doc invariant (`how-it-works.md:25` — "the marker carries the actual round number N") and the contract line's own `f"planned:{n}"`. Confirmed no 18.2.1 test pins the literal written by `main.py` (they assert dispatch/validation only; the only `process_task` test at `test_main.py:937` drives `review_failed:3`, untouched here).

- **Task 3.2** (new `planned:{attempt+1}` after the re-plan, end of loop body): Correctly closes the plan-side gap. `plan_review_failed:{attempt}` at line 301 stays and guards the crash-during-re-plan window; the new marker guards the crash-during-review-N+1 window. Placement is valid — at `attempt == max_iterations` the code raises at line 294-298 before reaching the re-plan, so no `planned:{max+1}` is ever written.

- **Task 3.3** (`main.py:329`, `f"implemented:{iteration}"`): Verified line 329 and the surrounding loop. `iteration` is the correct ordinal; the line serves both `review` and `test_run`. The `iteration == counter` short-circuit (`main.py:322-324`) and `impl_start` derivation (`main.py:315`) correctly consume the resumed counter so implement is skipped and `review-N.md` is written fresh. Guards at `main.py:316-320` / `:322-324` left untouched as instructed.

- **Task 4** (`tests/test_main.py:1166`): Confirmed the fixture seeds bare `"implemented"` and asserts `("review", 1)`. Under the clean break bare `implemented` falls to the heuristic and, with no plan-review files on disk, returns `("plan_review", 1)` — the test would break. Changing the fixture to `"implemented:1"` restores the assertion through the explicit branch. The four bare-`"planned"` fixtures the plan leaves untouched (`:546, :569, :596, :711`) were each traced: they exercise the git-adoption / no-git heuristic path (validate returns bare marker as-is → no dispatch branch matches → heuristic → `("plan_review", 1)`) and still pass. The plan's decision to leave them is correct.

- **Task 5** (Herald sidecar): Verified `/Users/max/projects/repo-stats-herald/.ai-factory/plans/34-6-2-coordination-root-seeding.json` already reads `"step": "implemented:3"` with `planner`/`implementer`/`elapsed` intact. Verify-only guard is appropriate; no rewrite needed.

### Critical Issues
None.

### Positive Notes
- The DEVIATION on Task 3.1 is a genuine catch: the implementer reconciled the spec's literal-`1` sketch against ground truth (line 277 is re-entered on resume) and chose the value the spec's own invariant and the contract line demand. Annotated transparently.
- Every bare-marker call site and every affected test fixture is enumerated and dispositioned — no silent gaps. The disjoint-prefix reasoning for dispatch/validation ordering is spelled out and holds.
- The Verify section's two reasoning traces (implement side and plan side, including the crash-during-re-plan window) match the actual control flow.

PLAN_REVIEW_PASS
