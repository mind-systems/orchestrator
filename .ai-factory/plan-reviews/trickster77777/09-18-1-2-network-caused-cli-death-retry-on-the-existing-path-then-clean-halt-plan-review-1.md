## Code Review Summary

**Files Reviewed:** 1 plan (targets `orchestrator/orchestrator/agents.py`; cross-checked `main.py`, `tests/test_agents.py`, specs 31 & 33)
**Risk Level:** 🟡 Medium

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): WARN — none. The change is confined to `agents.py` (`_run_claude` tail + `_classify_result` body), the pipeline boundary the roadmap contract assigns to 18.1. No module boundary crossed.
- **Rules** (`.ai-factory/RULES.md`): absent — gate skipped (WARN, optional file).
- **Roadmap** (`.ai-factory/roadmaps/trickster77777.md`): OK. Plan heading matches the `[ ] 18.1.2` contract line; the line's `Spec:` points at `31-network-cli-death-retry-then-halt.md`, whose "Depends on 18.1.1" points at `33-network-classifier-contract-red-tests.md`. The plan's 8-row table is byte-for-byte the table in spec 33; the retry/halt/no-new-constant constraints match spec 31 and the pinned contract in the phase header.
- **Skill-context** (`.ai-factory/skill-context/aif-review/SKILL.md`): absent — no project overrides to apply.

Line references in the plan were verified against the current file and are all accurate: stub body `agents.py:69-83`, tail `254-292`, extraction `251-252`, empty-stdout guard `272-275`, backstop `292`.

### Critical Issues
None that break at runtime.

### Findings

**1. The single `"error"` branch silently changes the `is_error`/exit-0 error message — the plan's "unchanged behavior" claim does not hold for that path.**

The classifier collapses two originally-distinct outcomes into one `"error"` verdict:
- Row 5 (`returncode != 0`, no rate-limit signal) — original message (`agents.py:267-270`):
  `f"Claude CLI failed with exit code {proc.returncode}\nstdout: {stdout ...}"`
- Row 7 (`is_error` true, and — because row 5 already caught nonzero — `returncode == 0`) — original message (`agents.py:280`):
  `f"Claude returned error: {result_text[:500]}"`

Task 2 instructs: `"error"` → `raise RuntimeError(...)` with the exit-code + stdout message, annotated "(unchanged behavior)". Applied literally, an `is_error` result with a clean exit 0 would now raise `"Claude CLI failed with exit code 0\nstdout: ..."` — a factually wrong "exit code 0" string, and a different first line (the one `cli()` forwards to the Telegram alert via `str(e).splitlines()[0]`, `main.py:511`). This contradicts spec 31's Behavior table ("`is_error`: unchanged — still surfaces as `RuntimeError`") and the plan's own "(unchanged behavior)" note.

The exception *type* and control flow are preserved; only the message regresses — hence Medium, not Critical. Fix: in the `"error"` branch keep both original messages by re-branching on the raw inputs still in scope, e.g. `if proc.returncode != 0: raise RuntimeError(<exit-code+stdout msg>) else: raise RuntimeError(f"Claude returned error: {result_text[:500]}")`. Either specify that in Task 2, or state explicitly that consolidating the two messages is an accepted change (in which case drop the "unchanged behavior" wording).

### Positive Notes
- The decision table traces correctly against all six red assertions (`tests/test_agents.py:537-564`) and — critically — reproduces the original precedence for the non-network rows: retryable(529) → returncode → is_error, with the network rows (2,3) inserted so only the *no-result* nonzero exit is reclassified. Overloaded-exhausted and clean-success paths remain byte-for-byte.
- The retry-wording branch keyed on `not parsed_final` is sound: row 1 (overloaded) can only fire with a populated `parsed_final` (empty `result_text` matches neither substring), so the "API overloaded" vs "network blip" split is unambiguous.
- Ratelimit consolidation (rows 4 & 6 → `RateLimitError(result_text)`) is genuinely unchanged — both original branches used the identical constructor.
- Purity of `_classify_result` is correctly preserved (no `sleep`/print/guard folded in), and the empty-stdout guard is correctly kept inline on the `"ok"` path — matching spec 33's explicit "do not fold it in".
- `NetworkError(HaltError)` flow-through was confirmed against `main.py:507-513`: the `except HaltError` block catches the subclass, prints `HALTED`, and `sys.exit(0)`. Leaving that block and `notify.py` untouched is correct.

### Deferred observations
None.
