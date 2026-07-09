# Plan: Tests-first: alert colour mapping + `cli()` exception routing

## Context
Pin the silent-failure surfaces that task 05 (yellow `halt` signal) will change: the `notify()` emoji mapping + gating, `cli()` exception→alert-type routing, and the exception *type* raised at the usage-gate and resume-past-max sources. Assertions on the not-yet-built `halt`/`HaltError` behaviour are red by design until task 05 lands; assertions on unchanged behaviour pass now.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Key constraints (read before writing any test)
- **Files must collect and import cleanly.** `HaltError` does not exist yet (task 05 adds it to `agents.py`). Never `from orchestrator.agents import HaltError` at module top — that is an `ImportError` (collection error), not a clean red assertion. Fetch it dynamically: `HaltError = getattr(agents, "HaltError", None)` and assert against it (`assert HaltError is not None and isinstance(...)`). The `assert HaltError is not None` is the red-by-design line now; it turns green once 05 defines the class.
- **Never hit the network.** Always monkeypatch `orchestrator.notify.send_telegram` (or the `subprocess`/usage reader). No real HTTP, no real `claude` CLI, no git subprocess on the tested paths, no agent LLM calls.
- **Assert only on the emoji prefix and the `alert_type`** — never on message wording (not a silent-failure surface).
- Build `OrchestratorConfig` directly from `orchestrator.config` (dataclass with keyword args), not via `load_config()` — avoid touching the real config file.

## Tasks

### Phase 1: `tests/test_notify.py` — emoji mapping + gating

- [x] **Task 1: Emoji-prefix mapping tests**
  Files: `tests/test_notify.py`
  Create the new file. Add a small local helper that builds an `OrchestratorConfig` with telegram enabled (`telegram_bot_token="t"`, `telegram_chat_id="c"`, `telegram_alerts=[...]` covering every alert type under test). Monkeypatch `orchestrator.notify.send_telegram` with a recorder that appends the outgoing `text` to a list (never calls the real function). For each `alert_type`, call `notify(config, "some message", alert_type)` and assert the captured text's **leading character(s)** are the expected emoji:
  - `stop` → 🔴 (green now)
  - `halt` → 🟡 (**red now** — current code maps everything outside `_FAIL_ALERTS` to 🟢; task 05 adds `_HALT_ALERTS`)
  - `milestone` → 🟢 (green now)
  - `done` → 🟢 (green now)
  - an unknown type e.g. `"whatever"` → 🟢 (green now)
  Reference the existing single-file test style in `tests/test_main.py` (one function per case, docstring stating expected behaviour).

- [x] **Task 2: Gating (silent no-op) tests**
  Files: `tests/test_notify.py`
  Using the same `send_telegram` recorder, assert `notify()` sends **nothing** (recorder stays empty) when:
  - `alert_type` is not present in `config.telegram_alerts` (e.g. config with `telegram_alerts=["milestone"]`, call with `"stop"`).
  - `telegram_bot_token` is `None` (but `alert_type` is listed and `chat_id` set).
  - `telegram_chat_id` is `None` (but `alert_type` is listed and `token` set).
  These pin the existing guards in `notify()` and are all green now.

### Phase 2: `tests/test_main.py` — `cli()` routing + source exception types

- [x] **Task 3: `cli()` exception-routing tests** (depends on Task 1 pattern for the `getattr` idiom)
  Files: `tests/test_main.py`
  Append a section with a local harness that, per test, monkeypatches: `orchestrator.main.load_config` → returns a test `OrchestratorConfig`; `orchestrator.main.run_implement` → raises the target exception; `orchestrator.main.notify` → records `(text, alert_type)` tuples into a list; and `sys.argv` → `["orchestrator", "implement", "."]`. Then call `main.cli()` and assert the recorded `alert_type`:
  - `PipelineStopError` → recorded `"stop"`, `cli()` exits via `SystemExit` (wrap in `pytest.raises(SystemExit)`). Green now.
  - `RateLimitError` (imported from `orchestrator.agents`) → recorded `"halt"`, exits via `SystemExit`. **Red now** (current `except RateLimitError` records `"stop"`); green after 05 re-routes it through `except HaltError`.
  - generic `Exception` (use a sentinel like `ValueError("boom")`) → recorded `"halt"` **and re-raised**: `with pytest.raises(ValueError): cli()`, then assert the recorder captured `alert_type == "halt"`. **Red now** (no `except Exception` in `cli()` today → propagates but `notify` never fires, so the `"halt"` assertion fails); green after 05 adds `except Exception` → notify `halt` → re-raise.
  Keep `RateLimitError` fetched via the normal import (it already exists); do not reference `HaltError` by name here — `RateLimitError` is the concrete family member exercised for the halt route.

- [x] **Task 4: Source-level exception-type tests** (depends on Task 3)
  Files: `tests/test_main.py`
  Two tests asserting the *type* raised at the source (both red until 05 re-points them from `PipelineStopError` to `HaltError`; use the `HaltError = getattr(agents, "HaltError", None)` idiom + `assert HaltError is not None and isinstance(exc.value, HaltError)`):
  - **Usage-threshold breach:** build a config with `usage_threshold_5h=90`, monkeypatch `orchestrator.main.subprocess.run` to return an object whose `.stdout` is `"Current session: 99%"` (over threshold, deterministic, no `claude` call). `with pytest.raises(Exception) as exc: _check_usage_limits(config)` then the `HaltError` isinstance assertion. Currently raises `PipelineStopError` → red.
  - **Resume past `max_iterations`:** reuse the `_dms_dirs` fixture pattern to build `.ai-factory/{plans,plan-reviews,reviews}` under `tmp_path`; write the plan file, a sidecar `{"step": "review_failed:3"}`, the gating review artifact `reviews/01-slug-review-3.md`, and a passing plan-review `plan-reviews/01-slug-plan-review-1.md` ending with `PLAN_REVIEW_PASS` (satisfies the safety guard at `main.py:348`). With `config.max_iterations=3`, the detector yields `("implement", 4, plan_path)`; `4 > 3` raises at `main.py:356` **before** any agent/git call. Build a minimal milestone stub (object with `.slug="slug"`, `.title`, `.description`, `.line_number`) and call `process_milestone(tmp_path, milestone, 1, config)` inside `pytest.raises(Exception)`, then the `HaltError` isinstance assertion. Confirm no monkeypatching of agents/git is needed because the raise precedes them; if `process_milestone`'s agent constructors touch anything, keep them untouched (they are pure object construction). Currently raises `PipelineStopError` → red.
