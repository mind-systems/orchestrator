# Review: Validate sidecar `step` against disk in resume detection

## Scope

- `orchestrator/main.py` — new `_validate_sidecar_step()` helper (lines 63–109), wired into `_detect_milestone_step()` (line 148) and `_detect_test_milestone_step()` (line 394).

## Verification against the plan

| Plan requirement | Implementation | Verdict |
|---|---|---|
| `"planned"` always valid | helper short-circuits via `step_value in ("planned", "implemented")` | OK |
| `"plan_review_failed:N"` requires `plan-reviews/{seq}-{slug}-plan-review-N.md` | explicit branch with path `plan_reviews_dir / f"{seq}-{slug}-plan-review-{n}.md"` | OK |
| `"plan_reviewed"` requires ≥1 plan-review ending with `PLAN_REVIEW_PASS` | explicit branch using `any(...)` over glob | OK |
| `"implemented"` always valid | covered by short-circuit | OK |
| `"review_failed:N"` requires `reviews/{seq}-{slug}-review-N.md` (implement mode) | passed via `fail_prefix="review_failed:"`, `fail_suffix="-review-{n}.md"`, `artifact_dir=reviews_dir` | OK |
| `"test_run_failed:N"` requires `test-runs/{seq}-{slug}-test-N.txt` (test mode) | passed via `fail_prefix="test_run_failed:"`, `fail_suffix="-test-{n}.txt"`, `artifact_dir=test_runs_dir` | OK |
| Defensive `int(...)` parse | `try/except (IndexError, ValueError)` around all `:N` branches | OK |
| Unrecognized → fall through | helper returns step_value as-is; dispatch's existing fall-through still applies | OK |
| Canonicalized `seq` used | both call sites pass the post-canonicalisation `seq` | OK |
| Task 3 helper extracted | done; both detect functions now use the helper | OK |

## Correctness analysis

**Prefix-collision check.** Order of branches in the helper:
1. `("planned", "implemented")` — exact match.
2. `startswith("plan_review_failed:")` — distinct prefix.
3. `== "plan_reviewed"` — exact match.
4. `startswith(fail_prefix)` — either `"review_failed:"` or `"test_run_failed:"`.

`"plan_review_failed:"` is matched before `"review_failed:"`, so a value like `"plan_review_failed:2"` in implement mode (where `fail_prefix="review_failed:"`) is correctly routed to the plan-review branch, not the review branch. No collision.

**Cross-mode stale values.** If a test-mode sidecar somehow contained `"review_failed:N"`, or an implement-mode sidecar contained `"test_run_failed:N"`, the helper returns it as-is (unrecognized) and the dispatch's own fall-through then routes execution to the heuristic. Safe.

**Parse guard.** The helper's `try/except` ensures any `:N` branch that survives validation has a parseable `n`. The downstream dispatch (`n = int(step_value.split(":")[1])`) is therefore safe without its own guard.

**Empty / unknown values.** Empty string short-circuits at the top of the helper. Unknown strings (e.g. `"foo"`) drop through every branch and return as-is, then fall through in dispatch. No behavioural change for those cases.

**Filesystem reads.** `plan_reviews_dir.glob(...)` with `read_text()` per file in the `plan_reviewed` branch is bounded by the small number of plan-review files per milestone (≤ `ORCHESTRATOR_MAX_ITERATIONS`, default 3). Negligible cost.

**Interaction with canonicalised `seq`.** The call sites pass the `seq` already adjusted by the `plans_dir.glob(f"*-{slug}.md")` block, so artifact paths line up with what the writer (`process_milestone` / `process_test_milestone`) actually produced even after a `_next_number()` drift. Correct.

**Downstream consumers.** For `step="plan", counter=N+1`, `process_milestone()` constructs `prev_plan_review = …-plan-review-{counter-1}.md` (i.e. `…-N.md`). The validator only lets `plan_review_failed:N` through when that file exists — so the original bug (planner receives a non-existent path) is closed.

When the validator clears `step_value`, the heuristic runs:
- If all plan-review files were deleted by rescue → step 3 returns `("plan_review", 1)` → fresh review on the (presumably refreshed) plan. Correct.
- If some plan-review files remain → steps 3–4 decide based on latest file. Reasonable.

## Minor observations (non-blocking)

1. **`plan_reviewed` lenience.** The validator accepts `plan_reviewed` if *any* plan-review ends with `PLAN_REVIEW_PASS`, while the heuristic (step 4) only inspects the latest. In practice the writer never produces a "passed then re-failed" sequence within a single milestone, so this divergence is theoretical. Plan-review-1 already noted this; no change required.

2. **No log line when validation clears a stale step.** A single `print(">>> Stale sidecar step '{step_value}' — artifact missing, falling back to heuristic")` would make rescue-induced fallbacks instantly visible in transcripts. The plan says "logging: minimal", so this is a judgment call; not a blocker, but worth considering as a tiny follow-up.

3. **Docstring vs. helper signature.** The helper's docstring describes the `<fail_prefix>N` rule generically ("`<fail_prefix>N` and the corresponding artifact … is missing") and is accurate. The doc does not list `review_failed:` and `test_run_failed:` by name, which is fine — the abstraction is intentional. No change needed.

4. **`f"{seq}-{slug}{fail_suffix.format(n=n)}"` micro-coupling.** Embedding a `{n}` template inside `fail_suffix` couples callers to a `str.format` contract. Works as written and only used twice, so refactoring isn't warranted; flagging only for awareness.

## Security / migration

- No new filesystem writes; only reads of files already trusted elsewhere in the function.
- No sidecar schema change; existing JSON sidecars remain compatible.
- No external input parsed; `step_value` originates from the orchestrator's own writes (or a trusted rescue skill).

## Verdict

Implementation matches the plan and closes the reported failure mode. No correctness bugs found. The minor observations above are advisory, not blocking.

REVIEW_PASS
