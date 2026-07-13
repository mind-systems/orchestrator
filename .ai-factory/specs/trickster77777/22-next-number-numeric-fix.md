# `_next_number`: pick by numeric max, not lexicographic last

**Date:** 2026-07-13
**Source:** conversation context (deferred observation on the `_next_number` tests milestone)

## Problem today

`_next_number` (`main.py:84`) picks the next artifact sequence index for a new plan/review/test file. It does:

```python
existing = sorted(directory.glob("*.md"))   # lexicographic string sort
if not existing:
    return 1
for f in reversed(existing):
    parts = f.stem.split("-", 1)
    if parts[0].isdigit():
        return int(parts[0]) + 1
return len(existing) + 1
```

It assumes the **lexicographically last** digit-prefixed file carries the **highest** number. That holds only while every number has the same width. The orchestrator writes numbers with `:02d` — a *minimum* width of two digits, not a fixed width — so at 100 the width grows to three digits and the assumption breaks. With `99-x.md` and `100-y.md` both present:

- lexicographic sort puts `"100-y.md"` **before** `"99-x.md"` (`'1'` < `'9'`);
- `reversed` yields `99-x.md` first;
- its prefix `99` is a digit → the function returns `99 + 1 = 100`;
- but `100-y.md` already exists → the new file is minted with an **already-used number** — a duplicate-artifact collision.

This is unreachable only while a single per-roadmap artifact dir (`plans/`, `plan-reviews/`, `reviews/`, or their per-stem subdirs) stays ≤ 99 files. On a long-lived project it will cross 100. It is the same lexicographic-vs-numeric trap Phase 2 fixed in `_resolve_claude`, in a different function.

## The fix

Replace the sort-and-take-last logic with a numeric maximum over the digit-prefixed files:

- Iterate every `*.md` in `directory`; for each, take `stem.split("-", 1)[0]` and, when it `isdigit()`, collect `int(...)`.
- If any digit-prefixed file exists → return `max(collected) + 1`.
- If none exists → keep the current `len(existing) + 1` fallback.
- Empty directory → return `1` (unchanged).

The sort is no longer load-bearing (drop it, or keep the glob unsorted). Numbering no longer depends on digit width.

## Contracts preserved (byte-identical)

- Empty dir → `1`.
- All-non-digit stems → `len(existing) + 1`.
- Uniform-width digit stems (`01`, `02`, `05`) → `max + 1` (same answer the old code gave).

The **only** behavior change is at mixed digit widths (≥ 100): `99-x.md` + `100-y.md` now yields `101`, not the already-used `100`.

## Tests

`tests/test_main.py` (the `_next_number` characterization suite the tests milestone wrote):

- The case that pinned the buggy mixed-width behavior — a `['9-a.md', '10-b.md']` set the old code resolved by lexicographic sort — must **flip** to assert the corrected numeric result (`max(9, 10) + 1 = 11`). This is intentional Class-A drift: the behavior changed by design; update the assertion, do not weaken it.
- Add the explicit boundary case: a dir with `99-x.md` and `100-y.md` → `101` (was the colliding `100`).
- The empty / single / uniform-width / all-non-digit / `08`+`09`→`10` cases stay green unchanged.

## Verify

- `uv run pytest` green, including the flipped mixed-width case and the new 99/100 boundary case.
- The empty and all-non-digit fallbacks return the same values as before.

## What NOT to do

- Do not change the empty-dir (`1`) or all-non-digit (`len + 1`) fallbacks.
- Do not touch `_next_number`'s callers — the fix is internal; the signature and return contract for the common cases are unchanged.
- Touch `main.py` and `tests/test_main.py` only.
