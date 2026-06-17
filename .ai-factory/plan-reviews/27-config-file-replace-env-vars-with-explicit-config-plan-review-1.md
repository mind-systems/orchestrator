# Plan Review: Config file — replace env vars with explicit config

**Risk Level:** 🟢 Low

## Verification Performed

I verified every concrete claim in the plan against the codebase:

- **Env-var call sites** — `grep "os.environ"` returns exactly the five reads the plan targets, at the exact lines stated:
  - L57 `ORCHESTRATOR_USAGE_THRESHOLD`, L58 `ORCHESTRATOR_WEEKLY_THRESHOLD` (in `_check_usage_limits`)
  - L658, L700 `ORCHESTRATOR_PHASE_SESSIONS` (in `_test_loop`, `_implement_loop`)
  - L749 `ORCHESTRATOR_MAX_ITERATIONS` (in `cli()`)
- **Call chain** — confirmed the full threading path: `cli()` → `run_implement`/`run_test` → `_with_caffeinate(_implement_loop/_test_loop)` → `process_milestone`/`process_test_milestone` + `_check_usage_limits()`. `_with_caffeinate` forwards `*args, **kwargs`, so passing `config` through works unchanged.
- **`_check_usage_limits()` callers** — currently called with no args at L666 and L708; Task 3 + Task 5 correctly cover both the signature change and the two call sites.
- **PipelineStopError "Bump ORCHESTRATOR_MAX_ITERATIONS" messages** — present at L351 and L591 (both functions); Task 4 covers both.
- **`import os` removal** — confirmed `os.` is used *only* by the five env reads being removed; after Task 5 nothing else in `main.py` uses `os`, so the conditional removal is correct. (`config.py` keeps its own `import os` for the `ORCHESTRATOR_CONFIG` read.)
- **No external callers** — none of the changed-signature functions are referenced outside `main.py` (`__init__.py`, `agents.py`, `roadmap.py`, `state.py`, `pyproject.toml` all clean). Entry point is `orchestrator.main:cli`, which is exactly where config loads. No hidden call sites to break.
- **`cli()` ordering** — `load_config()` at L749 sits *before* the `try` block (L751) that catches `PipelineStopError`/`RateLimitError`, so a `SystemExit` from `load_config()` propagates cleanly as the plan states.
- **Docs line numbers** — all verified accurate:
  - `docs/how-it-works.md` L7, L9 (`ORCHESTRATOR_MAX_ITERATIONS`), L35 (`ORCHESTRATOR_PHASE_SESSIONS`), L39 (`ORCHESTRATOR_USAGE_THRESHOLD`/`ORCHESTRATOR_WEEKLY_THRESHOLD`) ✓
  - `README.md` L48 "Env-переменные..." ✓
  - `.ai-factory/DESCRIPTION.md` L10 and L59 ✓
  - `CLAUDE.md` Key constants at L70, Commands section at L5 ✓
  - `docs/configuration.md` is indeed already written in the "Файл конфигурации" form with the exact field names — Task 6's "verify, don't rewrite" instruction matches reality.

The reference implementation in `.ai-factory/notes/12-config-file.md` is consistent with the plan and self-contained.

## Critical Issues

None.

## Minor / Optional Notes (non-blocking)

1. **Type-coercion errors aren't mapped to `SystemExit`.** The reference `load_config()` does `int(data["max_iterations"])` / `float(...)` without a try. If a user writes `"max_iterations": "three"` (or any non-numeric value), `int()`/`float()` raises an uncaught `ValueError` with a raw traceback instead of the clean exit used for the other three error cases. The plan's spec only mandates handling missing-file / invalid-JSON / missing-key, so this is out of declared scope — but wrapping the dataclass construction in a `try/except (ValueError, TypeError)` → `SystemExit(f"Invalid value in {path}: {e}")` would make the "no ugly tracebacks" UX consistent. Optional.

2. **`bool(...)` coercion is lossy for strings, but safe here.** `bool("false")` is `True`, so this would misbehave if `enable_phase_sessions` were a JSON *string*. Since JSON booleans parse to native Python `bool`, `bool(True)`/`bool(False)` round-trips correctly for well-formed config. No change needed; noting only so the implementer doesn't "improve" it into a string parser.

These are quality-of-implementation polish items, not correctness blockers for the stated scope.

## Positive Notes

- Line numbers, call chain, and doc references are precise — the plan was clearly written against the live code, not from memory.
- Task dependencies (1→2→3→4→5→6) are correctly ordered so the code never sits in a broken intermediate state within a commit.
- The commit plan groups changes sensibly (module+wiring, then env removal, then docs) and each commit is independently coherent.
- Correctly recognized that `docs/configuration.md` is already migrated and scoped Task 6 to verification rather than a redundant rewrite.
- The "remove `import os` only if nothing else uses it" guard shows the right caution — and it does turn out to be removable.

PLAN_REVIEW_PASS
