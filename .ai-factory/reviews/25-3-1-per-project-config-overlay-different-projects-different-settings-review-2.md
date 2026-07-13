## Code Review (re-review) — 3.1 Per-project config overlay

**Files re-read in full:** `orchestrator/config.py`, `orchestrator/main.py` (`cli()`), `tests/test_config.py`, `tests/test_main.py` change.
**Suite:** `uv run pytest` → 143 passed (was 142; +1 for the new non-object override test).

### Verdict on previous findings

**[Low] Well-formed but non-object override JSON crashes with an uncaught `TypeError` instead of a clean `SystemExit` — FIXED.**

Current `config.py:57-59`:

```python
            if not isinstance(override, dict):
                raise SystemExit(f"Config file is not valid JSON: {override_path}\nExpected a JSON object, got {type(override).__name__}")
            data.update(override)
```

The `isinstance(override, dict)` guard now sits between the `json.loads` and `data.update(override)`, so a well-formed non-object override (`[1,2,3]`, a bare string/number) raises a clean `SystemExit` naming the override path instead of the previous bare `TypeError` from `dict.update`. Regression-pinned by the new `test_load_config_non_object_override_json_raises_system_exit`, which writes `[1, 2, 3]` and asserts `str(override_path)` appears in the exit message — green in the run above. Verdict: **Fixed.**

### New review

Re-read all four changed files in full. No new correctness, security, or runtime issues.

- **Byte-stable absence** still holds — the whole override block is double-gated on `project_dir is not None` and `override_path.exists()`; when either is false `data` is untouched and the tail is the original code. Pinned by `test_load_config_no_override_is_byte_identical` (dataclass `==`).
- **Merge, guard order, required-key scoping, `telegram_alerts` replace** — unchanged from the prior pass and still correct; the new `isinstance` check inserts cleanly before `data.update` without altering any of them.
- **`main.py` threading** and the **`test_main.py` lambda** adaptation are unchanged and correct.
- The new guard's message reuses the base loader's "Config file is not valid JSON" prefix for input that is technically valid JSON but not an object. This is a deliberate, harmless convention match (the message also states the actual type and names the path); not a defect.

REVIEW_PASS
