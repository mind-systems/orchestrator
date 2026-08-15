# Code Review: 21.4 — A halt's message opens with a fixed clause

## Code Review Summary

**Files Reviewed:** 4 changed (`orchestrator/agents.py`, `orchestrator/main.py`, `tests/test_agents.py`, `tests/test_main.py`) + 3 read in full for context and guard-checking (`orchestrator/usage.py`, `orchestrator/notify.py`, the `cli()` except arms in `main.py`)
**Risk Level:** 🟢 Low
**Tests:** `uv run pytest` — **220 passed**, 23.55s

The change is two message reshapes, one docstring, two test cases. Both reshapes match the spec's proposed text verbatim, both are covered by a test that drives the real raise site, and every guard in the spec holds.

### Verified against ground truth

Not taken on trust — each checked against the files after the change:

| Claim | Verified |
|---|---|
| `agents.py:357` raises `RateLimitError(f"Agent reported a rate limit\n{result_text}")` | ✓ exact; `result_text` untruncated |
| `main.py:152-155` opens with the fixed clause, variable part on line 2 | ✓ exact |
| `HaltError` docstring states the convention (`agents.py:150-158`) | ✓ behaviour only — no phase/plan/`.ai-factory` reference |
| `RateLimitError`/`NetworkError` docstrings unrestated | ✓ unchanged (`:161`, `:165`) |
| Six compliant sites byte-identical | ✓ `agents.py:347`, `:351`, `main.py:137`, `:321`, `usage.py:48`, `:52` — none appear in the diff |
| `compose()`, `report()`, `_WORDS`, `_ALERT_TYPES` untouched | ✓ `notify.py` is not in the diff at all |
| `main.py:511-517` untouched — `:513` prints `str(e)` in full, `:515` keeps the first-line cut | ✓ exact |
| No new exception type, no new field on `HaltError` | ✓ hierarchy unchanged |
| Touch-list respected | ✓ only the four spec'd files changed |
| No doc quotes either message | ✓ `docs/` mentions only the two behavioural rows (`fault-handling.md:33`, `:57`), which describe what the run does, not message text |

**All eight halt sites now open with a fixed clause.** The two reshaped ones plus: two `NetworkError`s whose only substitution is `proc.returncode`; `main.py:137`'s literal; `main.py:321`'s counts (one logical line, wrapped in source, no path); `usage.py:48`/`:52`'s percentages.

**Consumers checked.** `str()` of a `HaltError` is consumed in exactly one place — `cli()`'s `except HaltError` arm. `usage.py` imports the type but never reads a message; `runtime.py` and `resume.py` neither catch nor inspect it. Nothing parses the old wording, so no reader breaks.

### Behavioural checks that hold

- **The rate-limit test genuinely reaches the raise.** With `result_text = "You hit your limit, resets at 5pm"` and `returncode = 1`: `_is_overloaded` false, `_is_transport_fault` false (no marker matches), `parsed_final` truthy so `no_result` false — the `returncode != 0 and "hit your limit"` branch at `agents.py:139` fires on attempt 1. No `time.sleep(RETRY_DELAY)` is entered, so the case is fast (0.32s for both new tests).
- **The fake process is sufficient and complete.** `_run_claude` touches exactly `.stdout` (iterated), `.wait()`, and `.returncode` before the raise at `:357`; `_FakeRateLimitProc` provides all three and nothing more. `state.active_proc` is cleared at `agents.py:311` before the raise, and the case additionally requests `clean_active_proc` — unconditional, matching the file's idiom.
- **`_CLAUDE_BIN` is patched, not resolved.** `_run_claude` calls `_resolve_claude()` only when the module global is `None`; monkeypatch sets it and restores it, so no real CLI lookup happens and no global leaks.
- **Both new tests actually guard the change.** Mutation-checked: reverting the two messages to their pre-change form makes exactly the two new cases fail (`test_run_claude_ratelimit_halt_has_fixed_first_line`, `test_resolve_roadmap_relpath_my_owner_mismatch_halt_has_fixed_first_line`) and nothing else; the tree was restored from the index afterwards and verified clean. These are not tautologies over a reconstructed string.
- **The second line can never leak into the first.** `relpath` is built from a slug and cannot contain a newline, and `first_line!r`/`expected_owner!r` are `repr`s — a newline inside a project's roadmap first line renders as an escaped `\n`, so `splitlines()[0]` stays the fixed clause for any input.
- **Degenerate inputs are safe.** An empty `result_text` yields `"Agent reported a rate limit\n"` — first line still fixed, and `compose()` skips a falsy detail only, which this never is.
- **No existing test depended on either wording.** `tests/test_main.py:923` builds `RateLimitError("boom")` directly; the two cases reaching `main.py:152` (`:1139` and `:1151`) both use a bare `pytest.raises(HaltError)` with no `match=`. All still pass.
- **The escalation path is unaffected.** `EscalationError` remains a sibling of `PipelineStopError`, not a `HaltError` subclass, and `cli()`'s escalation arm still passes `None` as its detail.

### Critical Issues

None.

### Findings

None.

### Nitpicks (non-blocking, no round warranted)

- `main.py:153` — the first fragment `f"Named roadmap owner line does not match the current git identity\n"` carries an `f` prefix with no placeholders. Behaviourally identical; it only matters if a linter is ever configured (ruff `F541`), and the project has none. The prefix also reads as deliberate symmetry with the interpolated second fragment beside it.

### Positive Notes

- **The test drives the raise site rather than reconstructing the message.** The spec allowed either; the chosen form is the one that catches a regression at `agents.py:357`, and the mutation check confirms it does. The fake process is minimal — three members, no more — instead of a general-purpose Popen mock that would rot as `_run_claude` changes.
- **The convention landed on the base class, once.** Stating it on `HaltError` and explicitly not restating it on `RateLimitError`/`NetworkError` puts the rule where every present and future halt site inherits it, with no copy to drift. The docstring explains *why* the first line matters (it becomes the notification's whole detail) rather than just asserting the shape, so a future author has the reason and not only the rule.
- **The negative half of the change is real, not assumed.** The six compliant sites, `notify.py`, and the `cli()` arms are genuinely absent from the diff — the guard held rather than merely being restated in the plan.
- **The owner-mismatch test asserts the split, not just the prefix.** Checking that the path and *both* identities live in the remainder proves the variable text moved rather than vanished, which is what keeps the console output honest.

## Deferred observations

- Affects: unknown (a future notification task) — The same first-line cut this task fixes for `HALTED` is applied unchanged to two sibling outcomes, where variable text still reaches the alert. `main.py:508` cuts `PipelineStopError`'s message for `UNCONVERGED`, and two of its four raise sites are single-line messages carrying variable text (`main.py:314` embeds `{seq}-{task.slug}`; `main.py:404` embeds `{task.title}`, read out of the project's own roadmap). `main.py:529` does the same for `ERRORED` over any unhandled exception, where `agents.py:365` raises `RuntimeError(f"Claude returned error: {result_text[:500]}")` — up to 500 characters of the agent's own text on one line. Invariant 5 of `docs/concepts/fault-handling.md` is written about notifications generally, not halts specifically, so the defect class is live on the siblings. Correctly out of scope here: spec `56` scopes itself to `HaltError` and its subclasses and pins the touch-list to four files.
- Affects: a future docs task on `docs/concepts/fault-handling.md` — The convention now lives only in the `HaltError` docstring. The docs tier carries the invariant it serves ("Its detail is therefore a short fixed label or nothing at all") but not the message shape that guarantees it, so a reader working from the concepts tier learns what a notification must not contain without learning how a raise site keeps it out. Out of scope here by the spec's explicit touch-list, which the plan recorded rather than worked around.
- Affects: the phase-19 durable–plan boundary work — `tests/test_agents.py` still carries two plan-layer coordinates as section dividers (`# Task 4: kill_active_child no-op branches` at `:462`, `# Task 6: kill_active_child killpg-failure fallback` at `:506`). The new section added by this task correctly names the surface instead (`# --- _run_claude rate-limit halt ---`), so the file is now mixed; the Phase 21 note settles that this coordinate is removed at the source rather than policed downstream.

REVIEW_PASS
