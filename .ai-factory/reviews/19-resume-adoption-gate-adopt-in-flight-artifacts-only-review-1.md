# Code Review: Resume adoption gate — adopt in-flight artifacts only

**Files reviewed (in full):** `orchestrator/resume.py`, `tests/test_main.py`, `docs/how-it-works.md`; cross-checked against spec `14-resume-adoption-gate.md`, `orchestrator/main.py` (caller context), and the ROADMAP line.

**Verdict:** No blocking correctness, security, or runtime defects. The change implements the spec faithfully; `uv run pytest` → **122 passed**.

## What was verified

- **Gate logic (`resume.py:60-109`).** `_plan_is_stale` returns `True` only on `returncode == 0` **and** empty `stdout.strip()` — i.e. tracked+clean. Every other branch (non-empty porcelain `??`/` M`/`A `, non-zero return code, raised exception) returns `False`. The candidate loop adopts the first (numerically lowest) non-stale candidate; if all are stale, `plan_path`/`seq` stay at the caller's fresh values. This matches the spec's fail-open-toward-re-planning-never-toward-`done` guard exactly.
- **Numeric sort, not lexicographic.** `candidates.sort(key=lambda c: c[0])` sorts on the parsed `int`, so 3-digit seqs don't reorder (`"100"` vs `"20"`). Correct.
- **Fresh-plan collision impossibility.** The caller passes `seq = _next_number()` = `max(existing) + 1` (`main.py`), so the fresh `plan_path` for a recurring milestone is always numbered above every on-disk plan and never exists → falls to step 1 → `("plan", 1, ...)`. The "all candidates stale → re-plan" path holds in production, not just in principle.
- **In-flight resume paths preserved.** Untracked (crash after plan write), staged-but-uncommitted (crash after review-PASS before `mark_done`+commit, staged by `git add -A`), and modified plans all yield non-empty porcelain → `False` → adopted. The four new tests pin committed-skip / untracked-adopt / staged-adopt / survivor-over-lowest, and the existing specs-08 matrix (untracked fixtures) stays green.
- **Dispatch table untouched.** `_validate_sidecar_step` and the step→(step, counter) mapping are byte-identical; the gate only filters which plan file feeds them.
- **Exception scope.** `subprocess.run` runs without `check=True`, so it never raises on non-zero exit; the `except Exception` catches only `FileNotFoundError` (git absent) / `OSError`, mapping them to `False`. Broad but correct for a fail-open helper.
- **`.ai-factory/` is tracked, not gitignored** (verified: no ignore rule; a committed plan reports `A `/clean, an in-flight one reports `??`/staged). So `git status --porcelain -- <plan>` returns empty *only* for committed-clean plans.

## Non-blocking observations (informational, no change required)

1. **Gitignore assumption is load-bearing.** The gate distinguishes stale from in-flight purely via porcelain output. A plan file that is *both untracked and gitignored* also yields empty porcelain and would be misread as stale (→ skipped → re-plan). This cannot happen for the orchestrator's own artifacts because it commits `.ai-factory/` via `git add -A`, and a target project that gitignored `.ai-factory/` would already be incompatible with resume-via-staged. The assumption is the same one the spec (`§ tracked and clean`) and docs sentence make explicit — flagged only so it stays visible if target-project requirements ever change.

2. **Caller-passed `plan_path` bypasses the gate.** If the caller ever passed a `seq`/`plan_path` that *already exists and is committed-clean* (rather than a fresh `_next_number` seq), the loop would skip it as a candidate but leave `plan_path` pointing at that same committed file, which exists → heuristic could return `done`. This never occurs today because `_next_number` always returns `max+1`. Purely latent; consistent with the spec's design contract.

3. **Doc wording nit (`docs/how-it-works.md:27`).** "адаптируется только незакоммиченный (in-flight) план" — «адаптируется» literally reads as *"is adapted/adjusted"*, not *"is adopted"*. «принимается»/«используется» would read more naturally. Cosmetic; meaning is clear from context.

REVIEW_PASS
