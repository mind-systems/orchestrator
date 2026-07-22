## Code Review Summary

**Files Reviewed:** 1 plan (targets `orchestrator/orchestrator/agents.py`; cross-checked `main.py`, `tests/test_agents.py`, specs 31 & 33, prior review-1)
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): OK — the change stays inside `agents.py` (`_classify_result` body + `_run_claude` tail), the pipeline boundary the roadmap contract assigns to 18.1. No module boundary crossed; `main.py`/`notify.py` are read-only dependents left untouched, per plan.
- **Rules** (`.ai-factory/RULES.md`): absent — gate skipped (optional file).
- **Roadmap** (`.ai-factory/roadmaps/trickster77777.md`): OK. Plan heading matches the `[ ] 18.1.2` contract line (line 79); the line's `Spec:` → `31-network-cli-death-retry-then-halt.md`, which "Depends on 18.1.1" → `33-network-classifier-contract-red-tests.md`. The plan's 8-row table, retry-on-529-path reuse, no-new-constant/no-backoff constraint, and `NetworkError(HaltError)`→`exit(0)` path all match specs 31 and 33 and the pinned contract in the phase header (line 76).
- **Skill-context** (`.ai-factory/skill-context/aif-review/SKILL.md`): absent — no project overrides.

Line references in the plan verified against the current `agents.py`: stub body `69-83`, tail `254-292`, extraction `251-252`, retry block `260-262`, row-5 message `267-270`, empty-stdout guard `272-275`, row-7 message `280`, backstop `292`. `main.py:511` (`str(e).splitlines()[0]` → Telegram alert) confirmed. All accurate.

### Critical Issues
None.

### Findings
None. Review-1's sole finding — that the single `"error"` verdict would collapse the row-5 (`exit code N`) and row-7 (`Claude returned error`) messages and emit a false `"exit code 0"` string on the `is_error`/exit-0 path — is now explicitly resolved in Task 2: the `"error"` branch re-branches on `proc.returncode` still in scope, preserving both first lines byte-for-byte (row-5 message when `returncode != 0`, row-7 message otherwise). This keeps the Telegram-forwarded first line unchanged and matches spec 31's Behavior table (`is_error`: unchanged → still surfaces as `RuntimeError`).

### Positive Notes
- **Decision-table equivalence verified by trace.** Because `no_result = not parsed_final` implies `result_text == ""` and `is_error == False`, the rate-limit substrings can never appear on a no-result row, so ordering rows 2–3 (network) ahead of rows 4–5 (returncode) introduces no conflict. Every non-network row (overloaded-retry, overloaded-exhausted, ratelimit-via-returncode, ratelimit-via-is_error, real error, ok) traces byte-for-byte to the original inline tail; only the *no-result nonzero exit* is reclassified — exactly the intended behavior change.
- **Empty-stdout guard placement is safe.** The `lines`-empty + `returncode == 0` case classifies as `"ok"`, so keeping the guard inline on the `"ok"` path before session-id/summary/return preserves the original `RuntimeError("...stdout is empty")`. The `lines`-empty + `returncode != 0` case is the network death the guard never reached originally (the returncode branch raised first) — now correctly routed to retry/`network_halt`.
- **Retry-wording branch is unambiguous.** `not parsed_final` distinguishes row 2 (network blip) from row 1 (overloaded), since row 1 requires a substring that an empty `result_text` cannot contain.
- **Purity preserved.** No `sleep`/print/guard folded into `_classify_result`; `MAX_RETRIES`/`RETRY_DELAY` and the single `for attempt` loop reused with no new constant or counter, per the owner-pinned contract.
- **Halt flow-through confirmed.** `NetworkError(HaltError)` is caught by `main.py:507-513`'s `except HaltError` → `HALTED` + `"stop"` alert + `sys.exit(0)`; leaving that block and `notify.py` untouched is correct.
- Test scope matches spec 31/33: filling the body turns the six red `test_classify_result_*` assertions (`tests/test_agents.py:537-564`) green; the `_run_claude` tail is a loud subprocess surface, correctly left to the reasoning-trace verify rather than a mock test.

PLAN_REVIEW_PASS
