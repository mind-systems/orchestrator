# Per-project config overlay

**Date:** 2026-07-13
**Source:** conversation context

> The governing behavior ТЗ for this feature lives doc-first in `docs/configuration.md` § Оверлей под проект (already written). This note holds the implementation mechanics that back that ТЗ; on any conflict the doc governs.

## Problem today

`load_config()` (`config.py:23`) reads a single global `orchestrator.json` — from the orchestrator repo root, or the `ORCHESTRATOR_CONFIG` env path — validates the four required keys, and returns one `OrchestratorConfig` that applies to **every** target project uniformly. `cli()` (`main.py:490`) calls `config = load_config()` before dispatching to `run_implement`/`run_test`. There is no way for project A to run with different settings (models are hardcoded, but `max_iterations`, `usage_threshold_5h`, `usage_threshold_weekly`, `enable_phase_sessions`, `telegram_*`, `roadmap_path`) than project B — the whole fleet shares one file.

## Target — a two-layer overlay keyed on the run's project

Introduce an optional **per-project override file** at `<project_dir>/.ai-factory/orchestrator.json` that layers over the global base. Precedence, lowest → highest:

1. `OrchestratorConfig` dataclass defaults (for the optional keys).
2. Global `orchestrator.json` (or `ORCHESTRATOR_CONFIG`) — the base, as today.
3. `<project_dir>/.ai-factory/orchestrator.json` — the per-project override.

### Signature change

`load_config(project_dir: Path | None = None) -> OrchestratorConfig`.

- With `project_dir is None` (or no override file present) behavior is **byte-identical to today** — this is the hard acceptance invariant.
- Load and validate the global base exactly as now: the four required keys are still required **in the global file**.
- Then, if `project_dir is not None` and `project_dir / ".ai-factory" / "orchestrator.json"` exists, parse it and **shallow-merge** its keys onto the base `data` dict *before* constructing `OrchestratorConfig`. Project keys override; keys absent from the override inherit the base value.

### Override file rules

- The four "required" keys are **not** required in the override — the base already supplied and validated them; the override carries only the keys it wants to change.
- The override reads the **same known key set** as the base (`max_iterations`, `usage_threshold_5h`, `usage_threshold_weekly`, `enable_phase_sessions`, `telegram_bot_token`, `telegram_chat_id`, `telegram_alerts`, `roadmap_path`). Unknown keys are ignored, consistent with how the base loader already only `.get()`s known keys.
- The override's `roadmap_path`, if present, passes through the **same guard** (`config.py:46`): absolute path or a `..` segment → `SystemExit` with the invalid-value message. It then flows through the existing three-state resolver (`_resolve_roadmap_relpath`, `main.py:125`) unchanged — including `"my"` (workstation-git-identity derivation, which at project scope resolves to that project's `.ai-factory/roadmaps/<slug>.md`).
- Malformed override JSON → `SystemExit` with a clear message naming the override path, mirroring the base's `json.JSONDecodeError` handling.
- The merge is **shallow** — `telegram_alerts` in the override **replaces** the base list, it does not concatenate. Pin this explicitly in a test so no one later assumes union semantics.

### cli() threading

`cli()` resolves the run's project directory from `args` (the path argument to `implement`/`test`, defaulting to the current dir) and passes it as `load_config(project_dir=...)`. The overlay must be applied **before** roadmap resolution, since `_resolve_roadmap_relpath` reads `config.roadmap_path` — which may now come from the override. The rest of `cli()` is unchanged.

## Forward-compat note

The not-yet-built REPL task (after `---STOP---`) plans per-command `implement <path>` / `test <path>` and a `load_config` return-type change. This overlay is compatible: a REPL would call `load_config(project_dir=<path>)` per command so each command re-resolves the correct project's overlay. This task adds only the optional parameter; it does not pre-empt the REPL's separate return-type change.

## Tests

Unit tests over `tmp_path` (pin in `tests/test_config.py`):

- **Byte-stable absence** — `load_config(project_dir=<dir with no .ai-factory/orchestrator.json>)` returns exactly the same config as `load_config()` with no argument. This is the acceptance invariant.
- **Precedence** — override sets `max_iterations` and a `telegram_chat_id`; result has the override values while un-overridden keys (`usage_threshold_5h`, etc.) keep base values.
- **Partial override** — an override with only `max_iterations` is valid even though it omits the other three "required" keys (base supplied them); no `SystemExit`.
- **`telegram_alerts` replaces, not merges** — base `["done"]`, override `["milestone-fail"]` → result `["milestone-fail"]`.
- **`roadmap_path` guard on the override** — override `roadmap_path: "/abs"` or `"../x"` → `SystemExit`.
- **Malformed override JSON** → `SystemExit` naming the override path.
- Point the global-base cases at the existing `test_config.py` coverage; do not duplicate base validation.

## Verify

- `uv run pytest` green before and after; the byte-stable-absence test proves zero behavior change for projects without an override file.
- A manual smoke: a project carrying `.ai-factory/orchestrator.json` with `{"max_iterations": 5}` runs with 5 iterations while the global stays at 3.

## What NOT to do

- Do not make `project_dir` required or change any existing call that passes no argument — absence stays byte-stable.
- Do not deep-merge or union list values — the overlay is a shallow key replace.
- Do not require the four base keys in the override.
- Do not touch the model hardcodes, the agent classes, or the roadmap resolver's three-state logic — only the source of `config.roadmap_path` widens.
- Do not conflate with `.ai-factory/config.yaml` (the AI-Factory project config, a different tool's file) — the override is its own `orchestrator.json`.
