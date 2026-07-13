# Plan: 4.1 — `_next_number`: pick by numeric max, not lexicographic last

## Context
Fixes the artifact-numbering collision in `_next_number` by choosing the next index from the numeric maximum of digit-prefixed stems instead of the lexicographically last one, so a per-roadmap artifact dir crossing 100 files (`99-x.md` + `100-y.md`) mints `101` rather than the already-used `100`.

## Settings
- Testing: yes (milestone explicitly requires updating and adding characterization tests)
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Fix the numbering logic

- [x] **Task 1: Replace lexicographic-last with numeric max in `_next_number`**
  Files: `orchestrator/main.py` (lines 84–93)
  Rewrite the body of `_next_number` so numbering no longer depends on digit width. Keep `existing = directory.glob("*.md")` (the `sorted()` is no longer load-bearing — drop it or leave the glob unsorted). Preserve the three contracts byte-identically per the spec (`.ai-factory/specs/trickster77777/22-next-number-numeric-fix.md`):
    - Empty dir → return `1`.
    - Iterate every `*.md`; for each take `f.stem.split("-", 1)[0]` and, when it `.isdigit()`, collect `int(...)`. If any digit-prefixed file exists → return `max(collected) + 1`.
    - No digit-prefixed file (all-non-digit stems) → keep the `len(existing) + 1` fallback (materialize the glob to a list so `len()` still works if the glob is consumed by the digit scan).
  Do not change the signature, the return contract for the common cases, or any caller. Touch `main.py` only in this task.

### Phase 2: Update and extend the characterization tests

- [x] **Task 2: Flip the buggy mixed-width characterization test** (depends on Task 1)
  Files: `tests/test_main.py` (`test_next_number_mixed_width_string_sort_boundary_characterization`, lines 1216–1224)
  This test currently pins the broken value (`['9-a.md', '10-b.md']` → `10`). Update it to assert the corrected numeric result: `max(9, 10) + 1 == 11`. Rewrite the docstring so it no longer describes "currently *broken*" / "pins the currently-produced value" behavior and instead documents the corrected max-based contract (the mixed-width set now resolves numerically, not by string sort). Rename the test if its `_characterization` name no longer fits (e.g. to reflect the corrected assertion) — keep it in the same section. This is intentional Class-A drift: update the assertion, do not weaken it.

- [x] **Task 3: Add the 99/100 → 101 boundary test** (depends on Task 1)
  Files: `tests/test_main.py` (same section, after the flipped test)
  Add a new test creating a dir with `99-x.md` and `100-y.md` and asserting `_next_number(tmp_path) == 101` (the old code returned the colliding `100`). Follow the existing test style (tmp_path fixture, `write_text("")`, descriptive docstring naming the width-boundary collision this guards against).

- [x] **Task 4: Refresh stale-mechanics docstrings in three adjacent tests** (depends on Task 1)
  Files: `tests/test_main.py` (lines 1167–1184 and 1200–1206)
  These three tests keep their assertions and names untouched — but their docstrings describe the removed `sorted`/`reversed`/first-match machinery, which no longer exists after Task 1. Rewrite only the docstring prose so it documents the corrected numeric-max mechanics:
    - `test_next_number_skips_later_sorting_non_digit_stem` (1167–1173) — drop the `sorted: [...]` / "reversed visits zz first, skips it" wording; describe that the non-digit stem contributes no number and the digit stem's `1` yields `2`.
    - `test_next_number_skips_earlier_sorting_non_digit_stem` (1176–1184) — drop the `reversed visits aa first` / "loop does not stop at the first non-digit stem regardless of where it sorts" wording; describe that non-digit stems are ignored irrespective of position and only digit stems feed the max.
    - `test_next_number_rolls_from_single_to_double_digit` (1200–1206) — drop "the padded convention under which lexicographic and numeric order agree… the risk is in the sort, not the int() parse"; describe that the max over `[8, 9]` yields `10`, independent of any sort or width.
  Assertions, test names, and fixtures stay identical — this is documentation accuracy only, keeping the suite from carrying descriptions of machinery the diff removed.

Note: the empty / single / gap / uniform-width / all-non-digit / `08`+`09`→`10` case *assertions* must stay green and unchanged — only the three docstrings named in Task 4 are edited; no other test bodies are touched.

## Verification
- `cd orchestrator && uv run pytest` green, including the flipped mixed-width case and the new 99/100 boundary case.
- Confirm the empty-dir (`1`) and all-non-digit (`len + 1`) fallbacks return the same values as before.
- Confirm the three refreshed docstrings (Task 4) no longer mention `sorted`/`reversed`/lexicographic order, and their assertions/names are unchanged.
