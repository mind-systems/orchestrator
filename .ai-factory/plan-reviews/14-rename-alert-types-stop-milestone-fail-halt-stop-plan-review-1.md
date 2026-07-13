## Plan Review Summary

**Plan:** Rename alert types: `stop`→`milestone-fail`, `halt`→`stop`
**Files Reviewed:** plan + spec note `specs/10-rename-alert-types.md` + targeted code (`notify.py`, `main.py`, `runtime.py`, `tests/test_notify.py`, `tests/test_main.py`, `docs/configuration.md`, `orchestrator.json.example`)
**Risk Level:** 🟡 Medium

### Context Gates
- **Roadmap (`ROADMAP.md`):** Plan title matches the pending milestone line "Rename alert types: `stop`→`milestone-fail`, `halt`→`stop`" exactly; it cites `Spec: .ai-factory/specs/10-rename-alert-types.md`. WARN-free — plan aligns with the contract line (pure rename, no behaviour change, runs last after 05/07/09, breaking-change note required, `telegram_alerts_example_all` addition required). All present in the plan.
- **Governing spec (`specs/10-rename-alert-types.md`):** Followed to leaf. The plan's five sweep areas map 1:1 onto the spec's sweep (notify.py sets, main.py handlers, tests, docs table, example config), the kebab `milestone-fail` spelling choice is honoured, the breaking-change meaning-flip note is carried, and the "do NOT touch `failures-and-halts.md`/`agents.py`/prompts" boundary is respected. One spec item is not reflected in the plan — see Deferred observations (live gitignored config).
- **ARCHITECTURE.md / RULES.md:** No `.ai-factory/ARCHITECTURE.md` or `RULES.md` present in the target; gate skipped. CLAUDE.md notes the file protocol is mirrored in the skills repo, but this milestone touches no artifact-protocol strings (PASS signals, sidecar fields, directory layout) — only Telegram alert-type tokens — so no cross-repo contract is affected. Correct.

I independently grepped every `"halt"`/`"stop"` alert literal across `orchestrator/`, `tests/`, `docs/` and cross-checked each against a task. Coverage is complete **except** for one site, below. All `~line` references in the plan are accurate against current source. `docs/failures-and-halts.md` confirmed to contain no alert-type literals (grep empty), matching the plan's assumption.

### Critical Issues

**1. Task 2 file scope is wrong — the force-quit `notify(..., "halt")` lives in `runtime.py`, not `main.py`.**
Task 2 declares `Files: orchestrator/main.py` and its four line references (~407/~328/~414/~417) are all main.py sites. It then adds, conditionally: *"If `_handle_sigint` force-quit issues a manual `notify(..., "halt")`, change that literal to `"stop"` too."* That call is real and unconditional — but after milestone 09 ("Extract main.py helpers into cohesive modules") `_handle_sigint` was moved to `orchestrator/runtime.py`, where the literal now sits at `runtime.py:20`:
```
notify(state.config, f"Orchestrator force-quit: {state.project_dir.name}\nRan for {_run_elapsed()}", "halt")
```
`main.py` no longer contains `_handle_sigint` at all. An implementer working Task 2 with file scope `orchestrator/main.py` will not open `runtime.py` and will leave this `"halt"` unrenamed. It also silently escapes the two-commit split: this edit belongs with Task 2's other `"halt"→"stop"` renames in **Commit 1**, but Task 7's grep backstop (which does search `orchestrator/`) doesn't run until **Commit 2** — so at best it lands in the wrong commit, at worst it is missed if the verify grep is run loosely (the plan even permits "unrelated prose like halting", inviting a false all-clear on a real literal). Fix: add `orchestrator/runtime.py` to Task 2's `Files:` list and make the force-quit rename an explicit, non-conditional bullet (`runtime.py:20`, `"halt"` → `"stop"`), since the site provably exists.

**2. Wrong cross-reference in Task 2.**
Task 2 says the force-quit change is "(verify by grep in Task 6)", and Task 2's header note about the same. Task 6 is the docs edit (`docs/configuration.md`); the grep sweep is **Task 7**. Minor, but it's inside the artifact under review and would misdirect a reader chasing the safety net. Correct "Task 6" → "Task 7".

### Positive Notes
- Line-number anchors throughout the plan are accurate against the current tree — no drift from the 05/07/09 churn except the `runtime.py` scope gap above.
- Task 4 and Task 5 correctly call out refreshing the now-stale pre-05 docstrings (`test_notify.py:49` "current code has no `_HALT_ALERTS`"; `test_main.py:723/731` "red now — currently routes to 'stop'" / "cli() has no except Exception today") — a common miss on rename sweeps, handled here.
- The gating-test reasoning in Task 4 is sound: `test_missing_bot_token_sends_nothing` etc. use `"stop"` as an arbitrary *listed* type, and since `"stop"` remains a valid type post-rename (now yellow), their gating intent is preserved without edits — the plan correctly avoids over-editing them.
- Task 3 correctly notes `config.py` reads only `telegram_alerts` and ignores unknown keys, so `telegram_alerts_example_all` is inert self-documentation, and flags trailing-comma JSON validity.
- The breaking-change meaning-flip note (Task 6) faithfully carries the spec's "flag loudly" requirement, including a concrete corrected-set example.
- Docs language constraint (keep `configuration.md` in Russian) is stated explicitly — matches the surrounding text.

## Deferred observations
- Affects: operator / live runtime config (gitignored, outside the committed diff) — The governing spec (§5) says "The live `orchestrator.json` (gitignored) is updated during implementation", but no task covers it. The live file currently holds `"telegram_alerts": ["stop", "done"]` and `"telegram_alerts_example_all": ["stop", "milestone", "done"]` — after this rename the literal `"stop"` flips from 🔴 failure to 🟡 operational-stop, so the operator's own alerts change meaning silently and the `_example_all` sibling goes stale (missing `milestone-fail`). This lies outside the milestone's commit boundary (the file is gitignored and never staged), so it is not a blocking finding, but the operator should consciously re-choose their set (e.g. `["milestone-fail", "stop", "done"]`) and refresh the example sibling when this lands. [dismissed]
