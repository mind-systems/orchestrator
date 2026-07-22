## Code Review Summary

**Files Reviewed:** 1 plan (`10-18-2-1-marker-index-grammar-contract-red-tests-...md`), verified against `orchestrator/resume.py`, `tests/test_main.py`, and the governing spec `.ai-factory/specs/trickster77777/34-marker-index-grammar-red-tests.md`
**Risk Level:** 🟡 Medium

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): tests-only task on `tests/test_main.py`, no module-boundary or dependency impact. `resume.py` is correctly the "sidecar step detection / resume dispatch" support module. No issue. ✅
- **Rules** (`.ai-factory/RULES.md`): absent — WARN, optional, nothing to enforce.
- **Roadmap linkage**: task **18.2.1** is present in `.ai-factory/roadmaps/trickster77777.md` (line 80) with a `Spec:` pointer to `specs/trickster77777/34-marker-index-grammar-red-tests.md`. Chain resolves cleanly. ✅
- **skill-context** (`.ai-factory/skill-context/aif-review/SKILL.md`): absent — no project overrides to apply.

### Critical Issues

**1. The plan over-asserts "red" for cases the governing spec explicitly calls out as green — and Task 5's acceptance criterion is thereby unsatisfiable.**

The spec is deliberate about a distinction the plan collapses. Spec §12: *"Some assertions run red against today's code, some coincide with the current heuristic fallback."* Spec §14 titles the dispatch group *"the load-bearing, genuinely-red cases"* and annotates **only** `implemented:3` and `planned:2` with *(today: … red)* — it lists `implemented:1` and `planned:1` **without** the red annotation. Spec §22–23 marks **only** the malformed `:N` validation cases as *"red today."*

The plan drops this nuance and claims blanket redness. Ground-truth verification against `resume.py`:

- **`planned:1` dispatch (Task 3 sibling) is GREEN today, not red.** With the `_dms_dirs` fixture (plan file + sidecar, no plan-review files), `_validate_sidecar_step("planned:1", …)` returns `"planned:1"` unchanged via the passthrough at `resume.py:57`; the dispatch does not recognize it (`resume.py:121-134`) and falls to the heuristic, which — because no plan-review files exist — returns `("plan_review", 1, plan_path)` at `resume.py:138-139`. That is **exactly** the asserted tuple. Task 3's claim *"the `:N` form is unrecognized → heuristic, so these are **red**"* is false for `N=1`: `planned:1` coincides with the heuristic default (`N=1` collides with both the old hardcoded counter *and* the "first plan review" default, so it cannot distinguish the new grammar from current behavior).
  - (By contrast `planned:2` is genuinely red — heuristic returns counter `1`, assertion wants `2`. And `implemented:1`/`implemented:3`/`implemented:2`-test-mode are all genuinely red because the heuristic returns step `plan_review`, not `review`/`test_run`.)

- **The well-formed `:N` validation flips (Task 1) are GREEN today, not red.** `_validate_sidecar_step("planned:2", …)` and `("implemented:2", …)` both fall through to the passthrough return at `resume.py:57` and return the input unchanged — which equals the asserted `"planned:2"` / `"implemented:2"`. Only the malformed cases (`planned:abc` / `implemented:abc`) are red today. Task 1's statement *"These assertions run **red** against today's `_validate_sidecar_step` … the redness is the TDD signal … do not weaken it"* is wrong for the two well-formed flips.

- **Consequence — Task 5's done-criterion is factually unsatisfiable.** Task 5 says: *"Confirm the newly flipped/added `_detect_task_step`/`_detect_test_task_step` `:N` cases and the malformed-`:N` validation cases fail."* `planned:1` is a newly-added `:N` dispatch case that will **pass** (green), so an implementer following Task 5 literally will observe a green test where the plan demands a red one and conclude the contract is unmet — directly contradicting the spec's *"some coincide with the current heuristic fallback"* and its Verify clause *"no other suite regresses beyond these intended reds"* (a passing test is not a regression).

The produced test tuples themselves are correct and match the spec exactly — this is not a wrong-test problem. The defect is in the plan's characterization of red-vs-green and, critically, in the Task 5 completion gate that will misfire on the green cases. Fix by realigning the prose to the spec's own split:
  - Genuinely red (must fail): `implemented:3`, `implemented:1`, `planned:2` (implement dispatch); `implemented:2` (test-mode dispatch); `planned:abc`, `implemented:abc` (validation).
  - Coincides / green today, pins the grammar as a regression guard (must **pass**, not fail): `planned:1` (dispatch); `planned:2`, `implemented:2` (validation).
  - Scope Task 5's "must fail" list to the genuinely-red set, and treat the coincident-green cases as passing pins — matching spec §12 and §34.

**2. (Same root, minor) The heuristic fall-through result is mis-described in Tasks 2 and 3.**

Task 2 says the unrecognized `implemented:N` form *"falls to the disk heuristic → `("implement", …)"`* and Task 3 similarly implies an `implement`-side fallback. With the `_dms_dirs`/`_dtms_dirs` fixtures there are **no plan-review files**, so the heuristic returns at the earlier `("plan_review", 1)` branch (`resume.py:138-139`), never reaching the `implement` branches. The tests are still red where the spec says they are (step mismatch), so this does not change any assertion — but the incorrect mental model is what produced the Issue-1 redness overstatement. Correct the fall-through description alongside the fix for Issue 1.

### Positive Notes
- Every line reference in the plan is accurate against the current files: `resume.py:31` (bare always-valid tuple), `:57` (passthrough tail), `:122`/`:129` (bare dispatch); and `tests/test_main.py:66/72` (validation), `:102` (malformed pattern), `:264/277` (dispatch), `:642` (test-mode), helpers `_dirs`/`_call` (40–52), `_dms_dirs`/`_dtms_dirs`.
- The `(step, counter, plan_path)` tuples pinned in every task match the governing spec verbatim.
- Correct fixtures/helpers are named for each suite, and the guidance to reuse them verbatim keeps the new tests consistent with the surrounding style.
- Scope is correctly held to tests-only (`tests/test_main.py`); the plan repeatedly and correctly forbids touching `main.py`/`resume.py`, matching spec §37–42.
- Task dependencies (Tasks 2–4 depend on Task 1; Task 5 depends on 2–4) are ordered sensibly.
- Correctly preserves `test_validate_unknown_value_passthrough` (the generic heuristic-passthrough contract is genuinely unchanged).

The plan is well-targeted and the tests it specifies are correct, but its red/green characterization contradicts the governing spec and makes Task 5's completion gate misfire on the coincident-green cases. Correct the redness framing (Issues 1–2) before implementation.
