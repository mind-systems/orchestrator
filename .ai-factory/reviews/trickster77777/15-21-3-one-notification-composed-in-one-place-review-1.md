# Code Review: 21.3 — One notification, composed in one place

## Code Review Summary

**Files Reviewed:** the full diff of `orchestrator/notify.py`, `orchestrator/main.py`, `orchestrator/runtime.py`, `tests/test_notify.py`, `tests/test_main.py`, `tests/test_runtime.py`, each read in full rather than as a hunk; plus the governing spec `docs/concepts/fault-handling.md`, the task spec `.ai-factory/specs/trickster77777/54-one-notification-shape.md`, the contract line `roadmaps/trickster77777.md:115`, and `.ai-factory/ARCHITECTURE.md`
**Risk Level:** 🟢 Low — no correctness, security, or API defect found.

### Verification run

- `uv run pytest` — **218 passed**, 0 failed. Baseline was 211, and the diff adds exactly 7 cases (6 in `test_notify.py`, 1 in `test_main.py`), so every pre-existing test still passes and nothing was silently dropped.
- `grep -n "notify(" orchestrator/main.py orchestrator/runtime.py` — **zero hits**, as the spec's § Verify demands. The new `from .notify import Outcome, report` lines carry no parenthesis, so the check is genuinely satisfied rather than accidentally evaded.
- `grep -c "report(" orchestrator/main.py orchestrator/runtime.py` — **8 + 1 = 9**, exactly the nine call sites.
- AST walk over both modules confirms all nine `report(...)` calls pass **5 positional arguments, 0 keywords** — no site is short an argument or relying on a default that does not exist.
- `git diff HEAD --stat -- orchestrator/agents.py` — **empty**. The spec's hardest guard ("do not touch `agents.py` at all") holds: no `path` field on `EscalationError`, no raise-site edit, no `_escalation_excerpt` or `_write_session` change, so the sidecar's `escalation` record and the cross-repo artifact contract are untouched.
- `notify()` diffed line-by-line against `HEAD` — **byte-identical**. Its `config.telegram_alerts` gate, its `_FAIL_ALERTS`/`_HALT_ALERTS`/`_ESCALATION_ALERTS` emoji selection, and all five token strings survive unchanged, which is the contract line's stated guard.
- `_ALERT_TYPES` reproduces the eight tokens the sites passed before the change, verified pair by pair against the pre-change call sites in `git show HEAD:orchestrator/main.py`. A `telegram_alerts` list written before this task selects exactly the alerts it always did.

### Correctness checks that could have failed and did not

- **Definition order.** `compose()` and `report()` are defined *above* `notify()` in the module. This is safe: `report` resolves the module-global `notify` at call time, not at definition time. It also preserves the patch target the tests rely on — `monkeypatch.setattr(notify_module, "notify", ...)` reaches the name `report` actually looks up, which a `from … import` binding would not have.
- **No import cycle.** `notify.py` gains only `enum` (stdlib, so the module docstring's "stdlib only, no new dependencies" stays true) and keeps `OrchestratorConfig` behind `TYPE_CHECKING`. `run_summary` remains a parameter of `report()` rather than being fetched from `runtime`, which is what holds the one-way `runtime`→`notify` direction pinned at `ARCHITECTURE.md:48`.
- **Deleting `msg` in the `EscalationError` arm is safe.** `print(f"ESCALATED — {e}")` (`main.py:520`) reads `e`, not `msg`, and `msg` has no other use in that arm. The two arms that still assign `msg` (`:508`, `:515`) are unaffected — only one `except` arm ever executes.
- **The `ERRORED` detail is preserved character-for-character**, `if str(e) else ''` guard included, so an exception raised with no message still composes a detail naming what was raised instead of an empty one.
- **`_ALERT_TYPES[outcome]` cannot raise `KeyError`** — `test_alert_types_covers_every_outcome_with_the_pinned_token` pins the mapping as a whole-dict equality, so adding an `Outcome` member without a token fails the suite rather than blowing up at runtime inside an `except` handler.
- **Enum iteration is deterministic**, so `assert recorded == [_ALERT_TYPES[o] for o in Outcome]` is not order-flaky.
- **`compose()`'s `if detail:` treats `None` and `""` alike**, which is correct for every site: the four detail-less outcomes pass a literal `None`, and no site can produce an empty-string detail (`ERRORED` always has the class name in front).
- **The new `EscalationError` routing test reaches the arm it names.** `EscalationError` is a direct `Exception` subclass, not a `HaltError` subclass, so `cli()`'s third arm fires rather than the second — the assertion `recorded[-1] == (Outcome.ESCALATED, None)` is testing what it claims to test.

### Spec conformance

Every clause of `54-one-notification-shape.md` is implemented as written:

- § 3 envelope — word, project, detail when truthy, run summary always — matches `compose()` exactly, including the run summary now reaching `TASK_DONE` and `RUN_DONE`, neither of which carried one before.
- § 4 details — `TASK_DONE` the task title; `RUN_DONE`/`MANUAL_STOP`/`FORCE_QUIT`/`ESCALATED` none; `UNCONVERGED`/`HALTED` the first line of the message; `ERRORED` the class name and first line — all present, and no `_cap()` helper or length bound was invented.
- The **defect the task exists to close** is closed at the site: `main.py:522`'s `msg = str(e).splitlines()[0]` is deleted and `None` is passed, so the escalation alert no longer carries the artifact path or the model-prose excerpt. `test_cli_escalation_error_routes_to_escalated_with_no_detail` is the one assertion pinning it, and it would catch a future edit restoring that line.
- Defect #2 is closed: `Unconverged` and `Stopped` no longer share a word, and `test_words_covers_every_outcome_with_distinct_values` makes any future collision a test failure rather than a channel a person has to open messages to read.
- The spec's standing rule at § Tests (`:138`) is satisfied exhaustively, not selectively: `grep -in "notif"` over both rewritten test files returns only the two `from orchestrator.notify import Outcome` import lines. No test name, docstring, or section comment still names a call its module can no longer make — including the positive `test_runtime.py` case renamed to `..._reports_when_...`.
- The Phase 19 coordinate rule is honoured precisely. Census after the change: `test_main.py` 14, `test_runtime.py` 4, `test_notify.py` 2 — 20, down from 21. Exactly the one line this task rewrote (`test_runtime.py:173-174`) took its coordinate with it; the other twenty untouched lines kept theirs, and no sweep was performed.

## Deferred observations

- Affects: `.ai-factory/specs/trickster77777/54-one-notification-shape.md` § 4 / `docs/concepts/fault-handling.md:93` (rule 5) — rule 5 now reads "never a filesystem path, never a line an agent wrote", and two live raise sites still reach the `HALTED` detail in violation of it: `RateLimitError(result_text)` (`agents.py:350`) makes the whole exception message the agent's own result text, so `str(e).splitlines()[0]` is by definition a line an agent wrote; and `_resolve_roadmap_relpath`'s owner-mismatch `HaltError` (`main.py:152-155`) is a single line carrying a roadmap path plus a quoted line from the file. Both are exactly what § 4 ratified ("exactly as today"), and `agents.py` is out of this task's touch-list, so neither is a defect in this change — but the governing spec's rule is not yet fully honoured by the code beneath it. Carried unchanged from plan-reviews 1 and 2, where it was ruled out of scope for this task.
- Affects: `.ai-factory/specs/trickster77777/54-one-notification-shape.md` § 4 — the line cut is justified there on the grounds that these messages "open with a fixed summary clause and continue into a path or raw output, and the cut is what keeps the label and drops the rest". That holds for the two dominant `PipelineStopError` raises (`main.py:298`, `:354` → "Plan failed", "Implement failed"), but two others have no rest to drop because they are single-line: `:314-316` yields "No passing plan review found for task {seq}-{slug}. Cannot proceed to implementation." — carrying an artifact stem that current slugs make ~60 characters — and `:404-407` yields the whole two-sentence message including the task title. Neither is a path or agent prose, so both stay inside rule 5, but neither is a short fixed label either. Relevant to whoever next revisits the detail's bound.
- Affects: `tests/test_notify.py:180` — `test_report_passes_the_pinned_alert_type_to_notify_for_every_outcome` builds `_config([...five tokens...])` and then patches `notify_module.notify`, so the config it constructs is never read by anything under test. Harmless and arguably self-documenting about which tokens the loop would enable, but it is setup that no assertion depends on; a bare `None` or a comment would carry the same information. Cosmetic only — no behaviour rides on it.

REVIEW_PASS
