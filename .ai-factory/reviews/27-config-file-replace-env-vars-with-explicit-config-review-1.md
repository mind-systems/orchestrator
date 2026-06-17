# Code Review: Config file — replace env vars with explicit config

**Scope reviewed:** `orchestrator/config.py` (new), `orchestrator/main.py`, and the doc updates (`CLAUDE.md`, `README.md`, `docs/configuration.md`, `docs/how-it-works.md`, `.ai-factory/DESCRIPTION.md`). Verified against `git diff HEAD` and full reads of the changed Python files.

## Verification

### `orchestrator/config.py` — correct
- `OrchestratorConfig` dataclass has exactly the four required fields with the spec's types.
- `load_config()` resolves the path from `ORCHESTRATOR_CONFIG` (the only retained env var) with `~` expansion, then enforces, in order: file existence → valid JSON → all four required keys present. Each failure raises `SystemExit` with a clear, path-naming message. The not-found message includes a copy-pasteable example JSON. This matches the reference in `notes/12-config-file.md`.
- Type coercion maps JSON key `usage_threshold_5h` to the dataclass field `usage_threshold_5h` correctly.

### `orchestrator/main.py` — wiring is complete and consistent
- `from .config import OrchestratorConfig, load_config` added.
- All five env reads are gone. `grep` over the package confirms no `os.environ.get("ORCHESTRATOR_*")` remains except the single `ORCHESTRATOR_CONFIG` read in `config.py`, and `import os` was removed from `main.py` (the only remaining `os.*` use in the package is `os.replace` in `agents.py`, which keeps its own import).
- `config` is threaded through the entire call chain with no signature mismatches:
  `cli() → run_implement/run_test(project_dir, config) → _with_caffeinate(_loop, project_dir, config) → _implement_loop/_test_loop(project_dir, config, …) → process_milestone/process_test_milestone(…, config, …)` and `_check_usage_limits(config)`.
  Every call site was cross-checked against every signature; positional ordering (e.g. `process_milestone(project_dir, milestone, i, config, planner_prompt_name, roadmap_filename, …)`) is correct.
- `process_milestone` / `process_test_milestone` derive `max_iterations = config.max_iterations` once at the top, so the unchanged loop/guard logic keeps working.
- `_check_usage_limits` reads `config.usage_threshold_5h` / `config.usage_threshold_weekly`.
- Both resume-guard `PipelineStopError` messages were reworded to "Raise max_iterations in ~/.orchestrator.json to continue." — no stale env-var name remains in user-facing runtime strings.
- `cli()` ordering is sound: `config = load_config()` runs after `parse_args()`/`project_dir` resolution (so `--help` still works without a config file) and before the `try` that catches `PipelineStopError`/`RateLimitError`. `SystemExit` from a missing/invalid config therefore propagates to the interpreter, printing the message to stderr and exiting non-zero — the intended behavior.

### Docs — consistent with the change
- The four removed env vars no longer appear in any user-facing doc (`CLAUDE.md`, `README.md`, `docs/configuration.md`, `docs/how-it-works.md`, `DESCRIPTION.md`); remaining hits are confined to historical `.ai-factory/` artifacts (old notes/plans/reviews), which correctly record past state.
- `CLAUDE.md` gained the config-creation step and updated Key-constants entries; `docs/how-it-works.md` L7/L9/L35/L39 now reference config fields; `README.md` doc-index reads "Файл конфигурации"; `DESCRIPTION.md` references `max_iterations` in `~/.orchestrator.json`.

## No correctness, security, or runtime-breakage issues found
No type mismatches, no missing call-site updates, no broken control flow, no leftover env reads.

## Minor / optional (non-blocking — explicitly scoped out in plan reviews 1 & 2)

These do not affect a well-formed config and need not gate the commit:

1. **`bool(data["enable_phase_sessions"])` coercion.** A JSON *string* `"false"` would coerce to `True` (non-empty string is truthy). A well-formed config uses a JSON boolean, so this is fine in practice; only worth special-casing if defending against string values.
2. **Malformed numeric values raise an uncaught `ValueError`.** If `max_iterations`/`usage_threshold_*` hold a non-numeric value (e.g. `"abc"`), `int(...)`/`float(...)` raise `ValueError` with a traceback rather than the clean `SystemExit` message used for the other failure modes. Given the change's theme of "clear message for config problems," wrapping the coercion block in `try/except (ValueError, TypeError)` → `SystemExit` would make the last validation path consistent. This matches prior (env-var) behavior, so it is not a regression.

The implementation faithfully realizes the plan and is correct as written.

REVIEW_PASS
