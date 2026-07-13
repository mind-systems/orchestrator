# Code Review: 2.1 — Tests-first: pin `_resolve_claude` PATH/nvm resolution and semver ordering

**Scope:** `tests/test_agents.py` (test-only change; no product code touched).
**Risk level:** 🟢 Low — test additions only, but one test does not verify what it claims.

## What was checked
Every added test was traced against the actual `_resolve_claude` behavior (`orchestrator/agents.py:81-95`), including the real `sorted(..., reverse=True)` ordering for each fake-nvm tree. Monkeypatch targets, the `xfail(strict=True)` handshake, and the `FileNotFoundError` `match=` regex were all verified.

- Patch targets are correct: `agents.shutil.which` and `agents.Path.home` (module-level, not top-level), per spec note 19 § Instantiation. `Path.home` set as a zero-arg lambda resolves correctly through the class call `Path.home()`.
- PATH-hit (both), the three not-found cases, the multi-candidate happy path, and the partial-install skip were each confirmed green against current code with the expected return/raise.
- The RED semver test genuinely fails today (`sorted(['v9.0.0','v20.11.0'], reverse=True)` → `['v9.0.0', ...]`, so the resolver returns `v9.0.0`; the assertion demands `v20.11.0`). `xfail(strict=True)` keeps the suite green now and will flip to a hard failure once 2.2's fix lands — the correct primitive for "stays RED until 2.2".
- `_CLAUDE_BIN` reset is legitimately omitted: every test calls `_resolve_claude()` directly, which never touches the cache.

## Findings

### 1. `test_resolve_claude_non_dir_entry_tolerated` never exercises the non-dir path — false coverage (`tests/test_agents.py:246`)

The test builds a stray file `somefile` alongside a valid `v18.0.0/bin/claude` and asserts `v18.0.0` is returned. It passes, but not for the reason it claims. `_resolve_claude` iterates `sorted(nvm_base.iterdir(), reverse=True)`, and in reverse order `v18.0.0` sorts **before** `somefile` (`'v' (118) > 's' (115)`):

```
sorted(['somefile','v18.0.0'], reverse=True) -> ['v18.0.0', 'somefile']
```

So the loop hits `v18.0.0` on the first iteration, finds `bin/claude`, and returns immediately — `somefile` is **never** inspected. The stray-file / non-dir branch (`somefile / "bin" / "claude"` → `.exists()` on a bogus nested path) is not executed at all.

Consequence: this test provides no guard against the very regression it was written to catch (per spec case #59: "guards against an implicit assumption that every entry in `nvm_base.iterdir()` is a directory"). If 2.2 — or any later change — introduced a `node_dir.is_dir()` filter or an `.iterdir()`/`.glob()` call that raises on a plain file, this test would stay green and miss it.

**Fix:** give the stray entry a name that sorts *ahead of* the valid version dir in reverse order, so it is visited first and the tolerance path actually runs. Since sort is reverse-lexicographic, any name greater than `"v18.0.0"` works — e.g. `zzstray`, or a version-looking `v99-broken`:

```python
(node_dir / "zzstray").write_text("")   # sorts before v18.0.0 under reverse=True
v18 = _make_claude_bin(node_dir / "v18.0.0")
...
assert agents._resolve_claude() == str(v18)
```

With `zzstray` first, the loop evaluates `zzstray / "bin" / "claude"` (`.exists()` → `False`, no crash), then falls through to `v18.0.0` — exercising exactly the tolerance the test name promises.

## Verdict
The suite is otherwise faithful to the roadmap contract and spec note, and all ordering claims check out against the real sort behavior. Only finding #1 needs addressing — a low-severity but genuine test-effectiveness defect that lets a non-dir regression slip through undetected.
