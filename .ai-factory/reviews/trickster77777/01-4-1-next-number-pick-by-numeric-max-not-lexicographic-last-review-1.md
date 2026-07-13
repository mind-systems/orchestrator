## Code Review — 4.1 `_next_number`: pick by numeric max, not lexicographic last

**Files reviewed:** `orchestrator/main.py` (`_next_number`, lines 84–96), `tests/test_main.py` (the `_next_number` suite, lines 1160–1227). Diff scope matches the plan and the roadmap contract line exactly — only `main.py` + `tests/test_main.py` changed (plus the planning artifacts).

### Correctness

The rewrite replaces `sorted(glob) → reversed → first digit-prefix + 1` with a numeric max over digit-prefixed stems:

```python
existing = list(directory.glob("*.md"))
if not existing:
    return 1
numbers = [
    int(parts[0])
    for f in existing
    if (parts := f.stem.split("-", 1))[0].isdigit()
]
if numbers:
    return max(numbers) + 1
return len(existing) + 1
```

Verified against each contract in the spec (`22-next-number-numeric-fix.md`):
- **Empty dir → `1`** — preserved (early return before the scan). ✅
- **All-non-digit stems → `len + 1`** — `existing` is materialized to a `list` before the comprehension, so `len(existing)` survives the scan; the generator-consumption trap the plan flagged is correctly avoided. ✅
- **Digit-prefixed → `max + 1`** — numeric, width-independent. ✅
- **The fix:** `9`/`10` → `11` (was `10`), and `99`/`100` → `101` (was the colliding `100`). ✅

The walrus `(parts := f.stem.split("-", 1))` binds per-iteration and reads `[0]` on the same value it tests — no double-split, no stale binding. `int(parts[0])` runs only under `isdigit()`, so no `ValueError` on the common ASCII path (identical guard to the pre-existing code — no regression). Signature and the sole caller (`main.py:403`, `_next_number(plans_dir)`) are untouched, as scoped.

### Tests

- The characterization pin was flipped honestly: renamed `test_next_number_mixed_width_string_sort_boundary_characterization` → `test_next_number_mixed_width_resolves_numerically`, assertion `== 10` → `== 11`, docstring rewritten off the "currently *broken*" framing. Class-A drift handled as the plan required — corrected, not weakened.
- New `test_next_number_three_digit_width_boundary` pins `99`/`100` → `101` in the existing style.
- The three stale-mechanics docstrings (`skips_later_sorting_non_digit_stem`, `skips_earlier_sorting_non_digit_stem`, `rolls_from_single_to_double_digit`) are refreshed to describe the numeric-max mechanics; assertions, names, and fixtures unchanged. Adjacent tests that remained accurate (`no_digit_stems_falls_back`, `sole_double_digit_entry`) correctly left alone.

### Verification run

- `uv run pytest tests/test_main.py -k next_number` → 10 passed.
- `uv run pytest` → 181 passed. No regressions elsewhere.

No bugs, security issues, or correctness problems found.

REVIEW_PASS
