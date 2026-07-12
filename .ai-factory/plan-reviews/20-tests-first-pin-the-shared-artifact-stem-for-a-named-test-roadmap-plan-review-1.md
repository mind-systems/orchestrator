## Plan Review Summary

**Files Reviewed:** 1 plan (`20-tests-first-pin-the-shared-artifact-stem-for-a-named-test-roadmap.md`)
**Risk Level:** 🟢 Low

### Context Gates
- **Spec 16 (`16-tests-first-shared-test-stem.md`):** Governing spec followed faithfully. Plan Task 1 = spec change #1 (flip `test_artifact_subdir_named_tests_roadmap_uses_stem` to `"kg-wmservice"`), Task 2 = spec change #2 (add `_artifact_subdir("custom-tests.md") == "custom"`), and the "keep green" set (default-pair `None`, named-main `"kg-wmservice"`) is preserved. WARN: none.
- **Spec 17 (`17-artifact-subdir-strip-tests-suffix.md`):** The implementation counterpart. The plan correctly scopes production changes *out* — both new assertions are knowingly red until spec 17 strips `-tests`. Consistent with `Path("custom-tests.md").stem.removesuffix("-tests") == "custom"` and `Path("roadmaps/kg-wmservice-tests.md").stem.removesuffix("-tests") == "kg-wmservice"`.
- **Roadmap alignment:** Tests-first milestone on `ROADMAP_TESTS.md` surface (default pair → flat artifact dirs); no boundary/dependency concerns for a tests-only change.

### Verified Against Ground Truth
- `tests/test_main.py:1097-1099` — the current assertion is exactly `_artifact_subdir("roadmaps/kg-wmservice-tests.md") == "kg-wmservice-tests"`; the plan's line reference and target flip are accurate.
- `orchestrator/main.py:166-170` — `_artifact_subdir` returns `Path(relpath).stem` raw on the non-default branch, so today `custom-tests.md` → `"custom-tests"` and `roadmaps/kg-wmservice-tests.md` → `"kg-wmservice-tests"`. Both new/flipped assertions are therefore genuinely red now and turn green only after spec 17 — matching the stated intent.
- The "stay green" trio is real and untouched by this plan: `test_artifact_subdir_default_roadmap_is_flat` (`None`), `test_artifact_subdir_named_roadmap_uses_stem` (`"kg-wmservice"`), and `test_artifact_subdir_track_file_uses_stem` (`"ROADMAP.watch"`). The plan's Verification wording ("default-pair, named-main, and track-file assertions stay green") is accurate.
- "Exactly two red": after the flip, only the named-tests assertion and the new explicit-path assertion mismatch the raw-stem production; count is correct.

### Critical Issues
None.

### Positive Notes
- Correct red-until-fix framing with the precedent (07→05 pattern) named, so the code reviewer downstream understands the intentional red and won't treat it as a regression.
- Task 1 rightly frames the change as flipping a Class-A accidental pin (raw-stem behavior was never a decision), not re-litigating a designed contract — matches spec 16's reasoning.
- Plan carries no `## Test Command` section and is structured for implement-mode review — the right choice, since a deliberately-red suite cannot be validated by test-mode's exit-code gate.
- Scope guard is explicit and correct: `orchestrator/main.py` must remain untouched.

PLAN_REVIEW_PASS
