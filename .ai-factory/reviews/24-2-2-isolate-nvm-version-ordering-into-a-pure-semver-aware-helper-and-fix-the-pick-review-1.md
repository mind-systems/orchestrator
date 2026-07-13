# Code Review: 2.2 — Isolate nvm version ordering into a pure semver-aware helper

**Files reviewed (in full):** `orchestrator/agents.py`, `tests/test_agents.py`
**Verification:** `uv run pytest tests/test_agents.py` → 25 passed.

## Scope check
The diff touches exactly the two files the plan authorizes and nothing else. No new imports, no third-party dependency (`str.isdecimal` / `int` / built-in `sort` only), zero-dep constraint honored.

## Correctness

`_sorted_nvm_node_dirs` (`agents.py:81`) is correct against every clause of the spec:

- **Parsing** — strips a leading `v`, splits on `.`, accumulates the leading run of `isdecimal()` segments into an int tuple, stops at the first non-decimal segment (`v18.20.4-nightly` → `(18, 20)`). Empty run → `None`. Matches spec `20-...md:15`.
- **`isdecimal()` (not `isdigit()`)** — the finding-3 steer from plan-review-1 is implemented: `int()` accepts exactly the `isdecimal()` set, so no Unicode-numeric segment can reach `int()` and raise. Never-raises contract holds.
- **Ordering / no cross-type comparison** — parseable and unparseable are split into two lists; parseable is sorted by the int-tuple key alone (`key=lambda pair: pair[0]`, the `Path` never enters the comparison), unparseable by `.name`, then concatenated `parseable + unparseable`. An int-tuple is never compared against a string, and a `Path` is never compared — the cross-type trap is structurally avoided rather than merely unlikely.
- **Highest-first / the bug fix** — `[v9.0.0, v20.11.0, v10.0.0]` → `(20,11,0) > (10,0,0) > (9,0,0)`, so `v20.11.0` wins. The lexicographic defect (`v9` beating `v20`) is gone.
- **Unparseable last** — `system`, `lts`, `zzstray`, bare `v`, `""` all yield `None` and fall to the tail, ordered by string name.
- **Empty list** → `[]`, no raise.

`_resolve_claude` (`agents.py:116`) is byte-identical outside the single loop-header swap: the `shutil.which` PATH-hit early return, the `nvm_base.is_dir()` guard, the `candidate = node_dir / "bin" / "claude"` / `.exists()` body, the `FileNotFoundError` install message, and the `_CLAUDE_BIN` cache are all untouched. The candidate set passed to the loop is the same as before (`list(nvm_base.iterdir())`), only reordered — so partial-install skip and non-dir tolerance behave as before, now with a correct pick order.

## Runtime-failure analysis
- No exception path: the only operations on untrusted names are `str.startswith`, slicing, `split`, `isdecimal`, and `int()` guarded by `isdecimal` — none raise on any string. A non-`Path` input can't arrive (caller passes `list(nvm_base.iterdir())`).
- Sort is stable; output is deterministic as a function of input. (In the pathological case of two names collapsing to the same leading int-tuple — e.g. `v18.20` and `v18.20.x` — tie order follows input order; this does not occur in real nvm layouts and is outside the spec's concern.)
- No filesystem access in the helper (pure), matching the spec's "no filesystem" contract — the `.exists()` check stays in the resolver.

## Tests
- The strict-`xfail` marker was removed from `test_resolve_claude_semver_ordering_picks_true_latest`; it now passes as a normal green test (an XPASS-under-strict suite failure is thereby avoided).
- The stale reasoning in `test_resolve_claude_non_dir_entry_tolerated` (docstring + inline comment) is corrected to reflect that an unparseable name now sorts **last**; the assertion is unchanged and still valid.
- Three direct helper unit cases were added (semver-not-lexicographic ordering, unparseable-sorts-last, empty-list-never-raises), fulfilling the governing spec's `20-...md:30` requirement that plan-review-1 flagged as unowned.

## Verdict
No correctness, security, or robustness issues found. The plan's three prior-review remediations are all implemented, and the full suite is green.

REVIEW_PASS
