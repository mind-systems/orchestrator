# Code Review: Telegram configurable alerts (review 1)

## Scope
Reviewed `git diff HEAD` across `orchestrator/config.py`, `orchestrator/notify.py`, `orchestrator/main.py`, `orchestrator.json.example`. Read each changed file in full.

## Verification
- **`config.py`** — `field` imported from `dataclasses`; `telegram_alerts: list[str] = field(default_factory=list)` added after the optional telegram fields (correct ordering — follows other defaulted fields, no non-default-after-default error). Read via `data.get("telegram_alerts") or []`, not added to `required`. Correct.
- **`notify.py`** — `notify()` checks `alert_type not in config.telegram_alerts` then the credential guard, then delegates to `send_telegram`. `notify` is defined before `send_telegram`, but the reference is resolved at call time, so there is no `NameError`. `TYPE_CHECKING` import of `OrchestratorConfig` avoids a runtime circular import (`config` imports nothing from `notify`, but the guard is correct defensive form). `send_telegram` unchanged.
- **`main.py`** — import changed to `from .notify import notify`; confirmed via grep that no `send_telegram` references remain in `main.py`, so the dropped name causes no `NameError`. Both `cli()` exception handlers now call `notify(..., "stop")` with the spec'd first-line-only message format. Milestone alerts added after `_git_commit` on all four success paths (resume + normal completion in both `process_milestone` and `process_test_milestone`); no `mark_skipped` path notifies. `done` alert added before `break` in the dynamic loop's in-loop empty-pending check.
- **`orchestrator.json.example`** — `"telegram_alerts": []` appended, JSON remains valid.

All message formats match the spec exactly.

## Observations (non-blocking)

1. **`done` alert does not fire when the roadmap is already fully complete at startup.** In `_run_dynamic_loop`, the pre-loop check (`if not pending: print("All milestones are done!"); return`, ~line 645) returns before the `while` loop, so the `"done"` notification (~line 666) is only reached when the *last* milestone is processed inside the loop. Starting a run with everything already `[x]` sends no alert. This matches the plan's explicit instruction to leave the startup check unchanged, so it is by-design, not a defect — noted only so the behavior is understood: `"done"` means "the run finished the last pending milestone," not "the roadmap is complete."

No correctness, security, or runtime-breakage issues found. No migrations, type mismatches, or import cycles introduced.

REVIEW_PASS
