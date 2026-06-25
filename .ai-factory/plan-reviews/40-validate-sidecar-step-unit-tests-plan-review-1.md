# Plan Review: `_validate_sidecar_step` unit tests

**Plan:** `40-validate-sidecar-step-unit-tests.md`
**Risk Level:** 🟢 Low

## Context Gates

- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): No boundary/dependency concerns — this is a pure unit-test addition to the existing `tests/` package, no production code touched. PASS.
- **Rules** (`.ai-factory/RULES.md`): not present — WARN (optional file missing, non-blocking).
- **Roadmap** (`.ai-factory/ROADMAP_TESTS.md`): Milestone present at line 19 (`_validate_sidecar_step` unit tests). The plan's 11 cases, file-path formulas, and `main.py` line references match the roadmap spec verbatim. Linkage confirmed. PASS.

## Verification Against the Codebase

Every claim in the plan was checked against `orchestrator/main.py`:

- `_validate_sidecar_step` is defined at `main.py:108` — correct.
- Signature `(step_value, seq, slug, plan_reviews_dir, artifact_dir, fail_prefix, fail_suffix) -> str` — confirmed via runtime introspection.
- Import `from orchestrator.main import _validate_sidecar_step` resolves under `uv run` — confirmed.
- Plan-review-failed path `plan_reviews_dir / f"{seq}-{slug}-plan-review-{n}.md"` — matches `main.py:133`.
- `plan_reviewed` glob `{seq}-{slug}-plan-review-*.md` + `.strip().endswith("PLAN_REVIEW_PASS")` — matches `main.py:140-141`.
- Artifact path `artifact_dir / f"{seq}-{slug}{fail_suffix.format(n=n)}"` → `01-slug-review-1.md` — matches `main.py:148`.
- Implement-mode args `fail_prefix="review_failed:"`, `fail_suffix="-review-{n}.md"` — matches `main.py:195-196`.
- Target file `tests/test_main.py` exists at repo root (the only `tests/` dir; no second copy under `orchestrator/`) and already imports from `orchestrator.main`. Test command `uv run pytest tests/ -v` runs from repo root against the root `pyproject.toml`. Correct.

## Branch Coverage

All six branches of the function are exercised, each with success and stale/empty paths where applicable:

1. Empty short-circuit (`main.py:126`) → case 1 ✓
2. `planned` / `implemented` always-valid (`128`) → cases 2, 3 ✓
3. `plan_review_failed:N` (`130-137`) → cases 4 (present), 5 (missing), 10 (malformed `ValueError`) ✓
4. `plan_reviewed` (`138-144`) → cases 6 (pass file), 7 (no files) ✓
5. `<fail_prefix>N` / `review_failed:N` (`145-152`) → cases 8 (present), 9 (missing) ✓
6. Unrecognized pass-through (`153-154`) → case 11 ✓

Coverage is complete for the function's observable behavior.

## Suggestions (non-blocking)

- **Optional extra case:** the malformed-`N` `except (IndexError, ValueError)` guard is tested only on the `plan_review_failed:` branch (case 10), not on the `review_failed:` branch (`main.py:150-151`). Adding `review_failed:abc → ""` would symmetrically cover both `try/except` blocks. Not required for milestone acceptance.
- **Isolation:** each test must take its own `tmp_path` fixture (function-scoped by default) so file creation in one case cannot leak into another — the plan already specifies `tmp_path` per the notes; just ensure no module-level shared dirs are introduced.

## Positive Notes

- Plan notes correctly flag the most error-prone assumption up front: the function does **not** read any sidecar/JSON — `step_value` is passed in directly. This prevents the implementer from over-mocking.
- Path formulas and `main.py` line anchors are precise and were all confirmed accurate.
- Test-case descriptions follow the existing `should …` style already present in `tests/test_main.py`, keeping the file consistent.

The plan is accurate, complete, and ready to implement.

PLAN_REVIEW_PASS
