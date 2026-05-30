# Plan Review: Validate sidecar `step` against disk in resume detection

## Plan Review Summary

**Risk Level:** 🟢 Low

The plan correctly diagnoses the failure mode (stale sidecar `step` referencing a deleted artifact) and proposes a small, well-scoped hardening of `_detect_milestone_step()` / `_detect_test_milestone_step()`. Validation rules map cleanly to the actual writers and consumers in `process_milestone()` / `process_test_milestone()`. The fallback design — clearing `step_value` and letting the existing heuristic re-derive — is the right shape: it adds no new state and degrades gracefully.

### Context Gates

- **Architecture:** No `.ai-factory/ARCHITECTURE.md` present. (WARN, non-blocking — repo has not adopted that file.)
- **Rules:** No `.ai-factory/RULES.md` present. (WARN, non-blocking.)
- **Roadmap:** Milestone 23 is the active item in `ROADMAP.md`. Linkage is implicit via the plan filename `23-…`. OK.

### Correctness Verification

Cross-referenced each validation rule against the sidecar writers in `main.py`:

| `step_value`             | Written at             | Artifact validated by plan                                              | Consumer on resume                                                       | Verdict |
|--------------------------|------------------------|-------------------------------------------------------------------------|--------------------------------------------------------------------------|---------|
| `planned`                | L212, L447             | none (always valid)                                                     | enters plan_review loop at attempt 1                                     | ✅      |
| `plan_review_failed:N`   | L236, L471             | `plan_reviews_dir / f"{seq}-{slug}-plan-review-{N}.md"`                 | re-plans with `prev_plan_review = …-plan-review-{counter-1}.md` (= N)    | ✅      |
| `plan_reviewed`          | L226, L461             | any `…-plan-review-*.md` ending with `PLAN_REVIEW_PASS`                 | enters implement loop                                                    | ✅      |
| `implemented`            | L263, L496             | none (always valid)                                                     | enters review/test_run loop at iteration 1                               | ✅      |
| `review_failed:N`        | L277                   | `reviews_dir / f"{seq}-{slug}-review-{N}.md"`                           | re-implements; reviewer reads diff, not the prior review file directly   | ✅      |
| `test_run_failed:N`      | L513                   | `test_runs_dir / f"{seq}-{slug}-test-{N}.txt"`                          | bridged to `…-patch-{N}.md` then implementer re-runs                     | ✅      |

All artifact paths match the writer paths exactly (same `seq`, same `slug`, same suffix). Use of post-canonicalisation `seq` (resolved from `plans_dir.glob(f"*-{slug}.md")`) is the correct choice — without it, `_next_number()` drift would point validation at the wrong file.

### Strengths

- Defensive `int(step_value.split(":")[1])` wrapping is explicit; prevents a malformed sidecar from raising `ValueError`/`IndexError` and crashing the run.
- `"unrecognized → fall through"` semantics are preserved.
- Task 3 is correctly marked optional with a clear skip threshold; the duplication will be ~12–18 lines per site, so extraction is likely warranted, but leaving it to implementer judgment is fine.
- No new sidecar fields, no migration: existing JSON sidecars remain forward/backward compatible.

### Minor Observations (non-blocking)

1. **`plan_reviewed` lenience vs. heuristic.** The plan validates `plan_reviewed` by checking whether **any** `*-plan-review-*.md` ends with `PLAN_REVIEW_PASS`. The downstream heuristic (step 4 / L121) only inspects `plan_review_files[-1]`. In normal operation these agree, but if (hypothetically) review-1 passed and review-2 was written later and didn't pass, the plan's validator would treat `plan_reviewed` as valid while the heuristic would say "plan again". This corner case is implausible given the writer logic (we only ever fail-then-replan, never succeed-then-replan-from-scratch within a single run), so the lenience is harmless. Optional tightening: use `sorted(...)[-1]` to match the heuristic's "latest must pass" semantic. Not required.

2. **`implemented` always-valid is in scope, but worth noting.** The plan correctly excludes working-tree validation for `implemented` — the heuristic at steps 5–7 handles that. The only thing this plan guards against is artifact-file deletion by `milestone-rescue`, which doesn't touch the working tree. So the scoping is right; just flagging that an unrelated working-tree corruption would still surface via the heuristic, not via this validator.

3. **Task 3 helper signature.** The proposed signature `_validate_sidecar_step(step_value, seq, slug, plan_reviews_dir, artifact_dir, fail_prefix, fail_suffix)` is workable but a bit awkward because `plan_reviewed` and `plan_review_failed:N` both look in `plan_reviews_dir` while `review_failed`/`test_run_failed` look elsewhere. If extracted, a small dict-driven dispatch (mapping step prefix → resolver lambda) may read cleaner than threading prefix/suffix args. This is purely a style nit; either shape works.

4. **Logging.** Plan opts for "minimal" logging. Consider one `print` line when validation clears a stale `step_value` (e.g. `>>> Stale sidecar step '{step_value}' — artifact missing, falling back to heuristic`). It would make `milestone-rescue` → resume failures dramatically easier to diagnose in transcripts. Not a blocker; up to the implementer.

### Architectural Fit

The change stays inside `_detect_milestone_step()` / `_detect_test_milestone_step()` — the same pure-function boundary already responsible for resume detection. No new dependencies, no contract changes to callers (return shape `(step, counter, plan_path)` is preserved). Aligns with the file-mediated agent communication model.

### Security / Migration

- No security surface introduced (the change only consults filesystem state already trusted elsewhere in the function).
- No migration required (no schema or storage format changes).

PLAN_REVIEW_PASS
