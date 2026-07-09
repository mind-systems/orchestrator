# Plan: Rename alert types: `stop`→`milestone-fail`, `halt`→`stop`

## Context
Rename the two ambiguous Telegram alert-type strings so their names are self-documenting: red `stop`→`milestone-fail`, yellow `halt`→`stop`. Pure rename sweep across code, tests, docs, and the example config — no behaviour, colour, or gating change.

## Settings
- Testing: no
- Logging: minimal
- Docs: yes

## Notes / Assumptions
- Token spelling is kebab-case `milestone-fail` (spec allows either; pick one and use everywhere). Use `milestone-fail` in every string, key value, and doc.
- Colour/cause mapping is unchanged: red fires only on a milestone failure, yellow on an operational stop. Only the strings that name those two cases move.
- `docs/failures-and-halts.md` names no alert-type strings (concept + colour only) — do NOT touch it; the verify step confirms this by grep.
- `agents.py`, prompts, and the artifact protocol are out of scope.
- Docs are written in Russian — keep `docs/configuration.md` edits in Russian to match the surrounding text.

## Tasks

### Phase 1: Code + config

- [x] **Task 1: Flip the emoji-mapping set values in `notify.py`**
  Files: `orchestrator/notify.py`
  In the module-level sets change `_FAIL_ALERTS = {"stop"}` → `{"milestone-fail"}` and `_HALT_ALERTS = {"halt"}` → `{"stop"}`. The string values are the contract; the constant names are cosmetic — `_FAIL_ALERTS`/`_HALT_ALERTS` still read correctly (fail = red = `milestone-fail`, halt = yellow = `stop`), so keep the names and update the two comments above them to reflect the new members. No logic change to `notify()` — the three-way emoji pick stays identical.

- [x] **Task 2: Update the `notify(...)` call sites in `main.py` and `runtime.py`** (depends on Task 1)
  Files: `orchestrator/main.py`, `orchestrator/runtime.py`
  Change only the `alert_type` literal in the terminal handlers — leave message text, colours, and control flow untouched:
  - `main.py` line ~407 (`PipelineStopError` handler, "Orchestrator stopped: …"): `"stop"` → `"milestone-fail"`.
  - `main.py` line ~328 (manual graceful-stop at loop tail, "Orchestrator stopped (manual): …"): `"halt"` → `"stop"`.
  - `main.py` line ~414 (`HaltError` handler, "Orchestrator halted: …"): `"halt"` → `"stop"`.
  - `main.py` line ~417–420 (the generic `except Exception` notify): `"halt"` → `"stop"`.
  - `runtime.py` line ~20 (`_handle_sigint` force-quit, "Orchestrator force-quit: …"): `"halt"` → `"stop"`. (Milestone 09 moved `_handle_sigint` out of `main.py` into `runtime.py`; the literal provably lives there now — this rename is unconditional and belongs in the same commit as the other `"halt"→"stop"` renames.)
  Do NOT change the `"milestone"` (`main.py` lines ~153, ~270) or `"done"` (`main.py` line ~303) calls — those names are unaffected. Task 7's grep backstop confirms nothing was missed.

- [x] **Task 3: Add `telegram_alerts_example_all` to `orchestrator.json.example`** (depends on Task 1)
  Files: `orchestrator.json.example`
  Keep `"telegram_alerts": []` as the active opt-in default. Add a sibling reference key right after it enumerating every valid alert type with the final names: `"telegram_alerts_example_all": ["milestone-fail", "stop", "milestone", "done"]`. `config.py` reads only `telegram_alerts` and ignores unknown keys, so this sibling is inert self-documentation. Mind trailing-comma validity when inserting the new key.

### Phase 2: Tests + docs

- [x] **Task 4: Rename the alert-type strings in `tests/test_notify.py`** (depends on Task 1)
  Files: `tests/test_notify.py`
  Class-A rename drift — keep each test's intent, only move the strings:
  - `ALL_ALERTS` (line ~38): replace `"stop"` and `"halt"` with `"milestone-fail"` and `"stop"` (keep `"milestone"`, `"done"`, `"whatever"`).
  - Red test (`test_stop_alert_prefixed_red`, ~41): assert 🔴 for `notify(..., "milestone-fail")`; rename the function/docstring to name `milestone-fail`.
  - Yellow test (`test_halt_alert_prefixed_yellow`, ~48): assert 🟡 for `notify(..., "stop")`; rename the function/docstring to name `stop`.
  - Gating tests (`test_missing_bot_token_sends_nothing`, `test_missing_chat_id_sends_nothing`, `test_alert_type_not_listed_sends_nothing`, ~81–98): these exercise gating, not colour — where they use the arbitrary listed literal `"stop"`/`["stop"]`, keep them valid; the string still exists as a valid type, so intent is preserved. Update any docstring that still references pre-05 state (e.g. "current code has no `_HALT_ALERTS`") so it matches current code.

- [x] **Task 5: Rename the routing assertions in `tests/test_main.py`** (depends on Task 2)
  Files: `tests/test_main.py`
  Keep the routing intent, update expected strings and names:
  - `test_cli_pipeline_stop_error_routes_to_stop` (~714): expect `recorded[-1][1] == "milestone-fail"`; rename function/docstring accordingly.
  - `test_cli_rate_limit_error_routes_to_halt` (~722): expect `"stop"`; rename function/docstring.
  - `test_cli_generic_exception_routes_to_halt_and_reraises` (~730): expect `"stop"`; rename function/docstring.
  Refresh any docstrings that describe the old string or pre-05 behaviour so they match current code.

- [x] **Task 6: Update the alert-types table and example in `docs/configuration.md`** (depends on Task 1)
  Files: `docs/configuration.md`
  In the Telegram section (~69–82), in Russian:
  - Example array (~69): `["stop", "halt", "milestone", "done"]` → `["milestone-fail", "stop", "milestone", "done"]`.
  - Table rows (~79–80): 🔴 row key `stop` → `milestone-fail`; 🟡 row key `halt` → `stop`.
  - Add a short breaking-change note near the table stating the literal `stop` **flips meaning** (was 🔴 failure, now 🟡 operational stop): there is no automatic migration, so an operator carrying `["stop", …]` must consciously re-choose the new set (e.g. `["milestone-fail", "stop", "done"]`).

- [x] **Task 7: Verify the sweep is complete** (depends on Tasks 1–6)
  Files: (verification only)
  - `grep -rn '"halt"' orchestrator/ tests/ docs/` returns no alert-type literal (`orchestrator/` includes `runtime.py`; allow unrelated prose like "halting" in log strings — but a `notify(..., "halt")` call is never allowed).
  - Confirm no remaining `"stop"` literal *meaning the red failure*: the only `"stop"` alert literals left must be the yellow operational-stop ones (`main.py`/`runtime.py` manual/halt/force-quit handlers, gating-test fixtures). No `_FAIL_ALERTS`/red path references `"stop"`.
  - Confirm `docs/failures-and-halts.md` still names no alert-type strings (grep it — expect no `"stop"`/`"halt"`/`"milestone-fail"` literals).
  - `uv run pytest` is green — mapping and routing tests now assert the renamed strings with the same intent.

- [x] **Task 8: Update the live gitignored `orchestrator.json`** (depends on Task 1)
  Files: `orchestrator.json` (gitignored — not staged/committed)
  Per spec §5 the live config is updated during implementation. It currently holds `"telegram_alerts": ["stop", "done"]` and `"telegram_alerts_example_all": ["stop", "milestone", "done"]`, where the literal `"stop"` still meant 🔴 failure. Consciously re-choose the operator set to preserve intent under the meaning-flip — `"telegram_alerts": ["milestone-fail", "done"]` (keep the red failure alert; add `"stop"` only if the yellow operational-stop alert is also wanted) — and refresh the sibling to the full valid set `["milestone-fail", "stop", "milestone", "done"]`. This file is never committed; it does not enter either commit.

## Commit Plan
- **Commit 1** (after tasks 1–3): "Rename alert types in notify, main, runtime, and example config" — includes the `runtime.py` force-quit rename.
- **Commit 2** (after tasks 4–7): "Update alert-type tests and configuration docs for rename"
- Task 8 edits the gitignored live `orchestrator.json` — it is never staged and enters no commit.
