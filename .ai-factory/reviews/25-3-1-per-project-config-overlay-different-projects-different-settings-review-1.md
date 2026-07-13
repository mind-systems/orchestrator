## Code Review — 3.1 Per-project config overlay

**Files reviewed (in full):** `orchestrator/config.py`, `orchestrator/main.py` (`cli()`), `tests/test_config.py`, `tests/test_main.py` change.
**Suite:** `uv run pytest` → 142 passed.

### Correctness

- **Byte-stable absence holds.** The new block is gated on `project_dir is not None` *and* `override_path.exists()`. When either is false, `data` is untouched and the rest of the function is the original code verbatim, so the result is byte-identical to the no-argument call. The `==` dataclass comparison in `test_load_config_no_override_is_byte_identical` proves it. In the real `cli()` path `project_dir` is now always non-None, but the absent-override guard preserves identical behavior for every project without an override file.
- **Merge ordering is right.** `data.update(override)` runs *before* the `roadmap_path` guard and before construction, so an override-supplied `roadmap_path` flows through the same guard and the same three-state resolver, and override values reach `int(...)`/`float(...)`/`bool(...)` coercion unchanged. Required-key validation runs only against the base — partial overrides are accepted.
- **`telegram_alerts` replaces, not unions** — falls out of `dict.update` naturally; pinned by test.
- **`main.py` threading** — `project_dir` is resolved at line 488 before `load_config(project_dir=project_dir)` at 490, so the overlay applies before `run_implement`/`run_test` and thus before roadmap resolution. No other line changes.
- **`test_main.py` lambda fix** is the minimal correct adaptation — the call site uses the `project_dir=` keyword, and `lambda project_dir=None:` accepts it while keeping the existing CLI-routing tests hermetic.
- **Guard message names the base `path`, not the override path,** when an override-supplied `roadmap_path` is the offender. Per the governing spec this is intentional (only the malformed-JSON case must name the override path; the guard test asserts only the offending value appears). Not a defect.

### Findings

**[Low] Well-formed but non-object override JSON crashes with an uncaught `TypeError` instead of a clean `SystemExit`.**
`config.py:57` — if `<project_dir>/.ai-factory/orchestrator.json` parses to a JSON array/string/number rather than an object (e.g. file contents `[1,2,3]`), `json.loads` succeeds so the `JSONDecodeError` handler is skipped, and `data.update(override)` then raises `TypeError: cannot convert dictionary update sequence element #0 to a sequence` (verified by running it). The user gets a bare traceback rather than the tidy `SystemExit` the malformed-JSON path produces. The base loader tolerates this shape (its `key not in data` loop turns a non-dict base into a `Missing required key` `SystemExit`), so the override path is less robust than the base it mirrors. Low severity — requires a hand-written malformed override — but a one-line `isinstance(override, dict)` check before `data.update` (raising the same override-path `SystemExit`) would close the gap and match the spec's intent that a malformed override exits cleanly naming its path.

This is a non-blocking robustness note; the implementation is otherwise correct and faithful to the spec.
