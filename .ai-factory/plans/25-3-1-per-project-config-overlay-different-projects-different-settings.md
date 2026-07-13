# Plan: 3.1 — Per-project config overlay — different projects, different settings

## Context
Widen `load_config()` to layer an optional per-project `<project_dir>/.ai-factory/orchestrator.json` over the validated global base, so different projects can carry different orchestrator settings without editing the fleet-wide file — while absence of the override stays byte-identical to today.

## Settings
- Testing: yes (milestone explicitly requires unit tests in `test_config.py`)
- Logging: minimal
- Docs: no (governing ТЗ already written in `docs/configuration.md` § Оверлей под проект)

## Tasks

### Phase 1: Overlay in the loader

- [x] **Task 1: Add optional `project_dir` overlay to `load_config()`**
  Files: `orchestrator/config.py`
  Change the signature to `load_config(project_dir: Path | None = None) -> OrchestratorConfig`. Keep the existing global-base load, the four-required-keys validation, and the `roadmap_path` guard **exactly as today** operating on the base file — this is the byte-stable-absence invariant. After the base `data` dict is built and validated, and only when `project_dir is not None` and `project_dir / ".ai-factory" / "orchestrator.json"` exists: read + `json.loads` the override, catching `json.JSONDecodeError` → `raise SystemExit(...)` with a message naming the **override** path (mirror the base's existing decode-error handling at `config.py:37-38`). Shallow-merge the override onto `data` with `data.update(override)` (project keys win, absent keys inherit) **before** the `roadmap_path` guard and the `OrchestratorConfig(...)` construction, so the merged `roadmap_path` flows through the same guard (`config.py:46`) and the same `.get()`-of-known-keys construction (`config.py:49-57`) unchanged. Do **not** re-run the four-required-keys check against the override (base already supplied them) and do **not** special-case `telegram_alerts` — `dict.update` already replaces the list rather than unioning it. Unknown override keys are ignored for free since construction only `.get()`s known keys. Reorder the existing `roadmap_path` guard so it runs on the merged `data` (move it below the merge), keeping its message text and behavior identical.

### Phase 2: Thread the run's project dir

- [x] **Task 2: Pass the resolved project dir from `cli()`** (depends on Task 1) — DEVIATION: plan didn't mention it, but `tests/test_main.py::_run_cli_with` monkeypatches `load_config` with a zero-arg lambda that broke against the new `project_dir=project_dir` call site; updated the lambda to accept `project_dir=None` so the existing CLI-error-routing tests keep passing.
  Files: `orchestrator/main.py`
  At `main.py:490`, change `config = load_config()` to `config = load_config(project_dir=project_dir)`. `project_dir` is already resolved one line above (`main.py:488`) from the `implement`/`test` path argument (defaulting to `.`), so the overlay applies before `run_implement`/`run_test` and therefore before roadmap resolution (`_resolve_roadmap_relpath` reads `config.roadmap_path`). No other line in `cli()` changes.

### Phase 3: Tests

- [x] **Task 3: Pin overlay behavior in `test_config.py`** (depends on Task 1)
  Files: `tests/test_config.py`
  Add tests over `tmp_path`, reusing the existing `_write_config` helper (which sets `ORCHESTRATOR_CONFIG` to the global base) and adding a small local helper to write `<project_dir>/.ai-factory/orchestrator.json`. Do not duplicate base-validation coverage — point base cases at the existing tests. Cases required by the spec:
  - **Byte-stable absence** — with a base written and a `project_dir` that has no `.ai-factory/orchestrator.json`, `load_config(project_dir=that_dir)` returns a config equal to `load_config()` with no argument (compare the dataclasses / their fields).
  - **Precedence** — base + override setting `max_iterations` and `telegram_chat_id`; assert those come from the override while un-overridden keys (e.g. `usage_threshold_5h`) keep base values.
  - **Partial override** — override containing only `{"max_iterations": ...}` (omitting the other three "required" keys) loads without `SystemExit`.
  - **`telegram_alerts` replaces, not merges** — base `telegram_alerts` `["done"]`, override `["milestone-fail"]` → result exactly `["milestone-fail"]`.
  - **`roadmap_path` guard on the override** — override `roadmap_path` `"/abs"` and (separate case) `"../x"` each raise `SystemExit` whose message names the offending value.
  - **Malformed override JSON** — write invalid JSON into the override file → `SystemExit` whose message contains the override file path.
