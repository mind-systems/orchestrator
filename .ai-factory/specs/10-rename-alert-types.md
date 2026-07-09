# Rename alert types: `stop` → `milestone-fail`, `halt` → `stop`

**Date:** 2026-07-09
**Source:** conversation context

## Why

After task 05 the alert types are `stop` (🔴 milestone failure) and `halt` (🟡 operational stop). `stop` and `halt` are near-synonyms — the names don't say which is the failure and which is the benign stop. That ambiguity actively misled planning once already. Rename for self-documenting names:

- `stop` → **`milestone-fail`** (🔴 — the milestone could not be completed)
- `halt` → **`stop`** (🟡 — the orchestrator stopped for an operational reason)

This pairs cleanly with the existing greens: `milestone` (a milestone finished) vs `milestone-fail` (a milestone failed); `stop` (the run stopped) vs `done` (the run finished). The token spelling `milestone-fail` (kebab) is a cosmetic choice — `milestone_fail` is equally fine; pick one and use it everywhere.

## Ordering — runs LAST (after 09)

This is a pure rename sweep over settled code. Every task that introduces or references these type strings (05, 07, and their tests) lands first; this task renames the final result in one pass. No behaviour changes — only the string values and their references.

## The sweep

1. **`notify.py`** — the set membership that drives the emoji: the red set value `{"stop"}` → `{"milestone-fail"}`; the yellow set value `{"halt"}` → `{"stop"}`. Rename the internal constant (`_HALT_ALERTS`) to match its new meaning if it reads wrong; the constant name is cosmetic, the string values are the contract.
2. **`main.py` — `cli()` handlers and the manual paths:** `notify(..., "stop")` on the `PipelineStopError` handler → `"milestone-fail"`; every `notify(..., "halt")` (the `HaltError` handler, the generic `except Exception`, the graceful-stop at the loop tail, and the force-quit in `_handle_sigint`) → `"stop"`.
3. **Tests** — update the expected type strings in `tests/test_notify.py` and the `cli()`-routing assertions in `tests/test_main.py` (from task 07): red assertions expect `"milestone-fail"`, yellow expect `"stop"`. Class-A rename drift, not a behaviour change — keep the assertions' intent.
4. **`docs/configuration.md`** — the alert-types table: the 🔴 row key `stop` → `milestone-fail`; the 🟡 row key `halt` → `stop`; update the example `telegram_alerts` array to the new names. `docs/failures-and-halts.md` names no type strings (concept + colour only) — leave it; verify by grep.
5. **`orchestrator.json.example` — make the valid values discoverable.** Today it ships `telegram_alerts: []`, which hides what strings are accepted. Keep the active default `[]` (alerts stay opt-in) but add a sibling reference key `telegram_alerts_example_all` listing **every** valid alert type with the final names — `["milestone-fail", "stop", "milestone", "done"]` — mirroring the pattern already in the live `orchestrator.json`. `config.py` reads only `telegram_alerts` and ignores unknown keys (JSON has no comments), so the sibling is inert self-documentation the loader never touches. The live `orchestrator.json` (gitignored) is updated during implementation.

## Breaking change — flag loudly

This is **not** an additive change: the literal `stop` **flips meaning** (was 🔴 failure, becomes 🟡 operational stop). A config carrying `["stop", …]` keeps a valid-looking `stop` entry that now gates the yellow stop instead of the red failure. There is no automatic migration — an operator must consciously choose the new set (e.g. `["milestone-fail", "stop", "done"]`). State this in the `docs/configuration.md` note so the meaning-flip is not silent.

## Verify

- `grep -rn` finds no remaining `"halt"` alert-type literal and no `"stop"` literal meaning the red failure anywhere in `orchestrator/`, `tests/`, or `docs/`.
- `uv run pytest` green — the mapping/routing tests now assert the renamed strings, same intent.
- No behaviour change: same colours, same events, same gating semantics — only the names differ.

## What NOT to do

- Do not change behaviour, colours, or which cause maps to which colour — only the type-string names.
- Do not run before 05/07 — it renames what they produce.
- Do not touch the concept doc's wording (`failures-and-halts.md`), `agents.py`, prompts, or the artifact protocol.
