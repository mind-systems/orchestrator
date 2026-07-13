# Code Review (Re-review): 2.1 — Tests-first: pin `_resolve_claude` PATH/nvm resolution and semver ordering

**Scope:** `tests/test_agents.py` (test-only change).
**Result:** Prior finding fixed; no new issues.

## Verdict on previous findings

### Finding 1 — `test_resolve_claude_non_dir_entry_tolerated` never exercises the non-dir path (false coverage) — **Fixed**

Previous version placed a stray file named `somefile`, which sorts *after* `v18.0.0` under `reverse=True`, so the valid candidate was returned before the stray was ever inspected.

Current content (`tests/test_agents.py:240-251`):

```python
def test_resolve_claude_non_dir_entry_tolerated(monkeypatch, tmp_path):
    """A plain file sorting ahead of the valid version dir under
    reverse=True is visited first and tolerated without a crash, and the
    valid candidate is still returned."""
    fakehome = tmp_path / "fakehome"
    node_dir = fakehome / ".nvm" / "versions" / "node"
    node_dir.mkdir(parents=True)
    (node_dir / "zzstray").write_text("")  # sorts before v18.0.0 under reverse=True
    v18 = _make_claude_bin(node_dir / "v18.0.0")
    monkeypatch.setattr(agents.shutil, "which", lambda name: None)
    monkeypatch.setattr(agents.Path, "home", lambda: fakehome)
    assert agents._resolve_claude() == str(v18)
```

The stray entry is renamed to `zzstray`. Confirmed empirically that `sorted(['zzstray','v18.0.0'], reverse=True)` → `['zzstray', 'v18.0.0']`, so the loop now visits `zzstray` **first**: `zzstray / "bin" / "claude"` → `.exists()` returns `False` on the bogus nested path (no crash — the actual non-dir tolerance the test claims to guard), then falls through to `v18.0.0` and returns it. The test now genuinely exercises the branch, and the docstring was updated to describe the corrected setup. This closes the false-coverage gap: a future regression assuming every `iterdir()` entry is a directory would now be caught.

## Full re-review for new issues

Read the entire changed file; the only change since review 1 is the non-dir test fix above — all other tests are unchanged and were verified correct in review 1 (patch targets, both PATH-hit cases, three not-found raises, multi-candidate, partial-install, and the RED `xfail(strict=True)` semver test).

Ran the suite: `uv run python -m pytest tests/test_agents.py -q` → **21 passed, 1 xfailed**. The single xfail is the semver-ordering test, correctly RED against current code and pinned to flip to a hard failure once 2.2 lands.

No bugs, type mismatches, or correctness problems found. Test-only change; no product code, migrations, or runtime surface affected.

REVIEW_PASS
