## Plan Review Summary

**Plan:** 2.1 — Tests-first: pin `_resolve_claude` PATH/nvm resolution and semver ordering
**Files targeted:** `tests/test_agents.py` (test-only; no product code touched)
**Risk Level:** 🟢 Low

### Context Gates
- **Roadmap alignment (ERROR gate):** PASS. The plan maps to `.ai-factory/ROADMAP.md` line 79 (milestone **2.1**). Every enumerated case in the contract line is covered: PATH-hit returns `shutil.which` verbatim with the nvm branch never reached (Task 2); missing `~/.nvm`, empty node dir, and no-`bin/claude`-anywhere each raise `FileNotFoundError` with the install message (Task 3); partial installs skipped and non-dir entry tolerated (Task 4); and the `v9.0.0` vs `v20.11.0` ordering assertion pinned RED (Task 5). The RED-until-2.2 handoff matches roadmap line 81 (milestone 2.2). No missing milestone linkage.
- **Spec chain (`Spec:` note):** PASS. Follows `.ai-factory/specs/19-resolve-claude-cli.md`. The plan correctly applies the note's § Instantiation guidance (patch `agents.shutil.which` and `agents.Path.home`, build fake trees under `tmp_path`, keep `.exists()`/`.is_dir()` as real filesystem ops). It also correctly identifies and resolves the one place where the roadmap contract overrides the spec: spec case #47 documents the *buggy* `v9.0.0` pick as the expected value, whereas the milestone requires asserting the *correct* pick and pinning it RED. The plan flags this override explicitly (Task 5) — grounding is sound, not invented.
- **Architecture / Rules gates:** `.ai-factory/ARCHITECTURE.md` present; no boundary concerns (test-only change, no module dependencies added). No `.ai-factory/RULES.md` and no `.ai-factory/skill-context/aif-review/SKILL.md` present — nothing to enforce.

### Critical Issues
None.

### Verified Claims (spot-checked against ground truth)
- **Lexicographic sort really is RED for the chosen pair.** `sorted(["v9.0.0","v20.11.0"], reverse=True)` → `['v9.0.0', 'v20.11.0']`, so `_resolve_claude` (`agents.py:89`) iterates `v9.0.0` first and returns it. Asserting the resolver returns `v20.11.0` therefore fails against current code — the RED pin is genuine, not a phantom.
- **`match=` regex is safe.** The install message `npm install -g @anthropic-ai/claude-code` contains no regex metacharacters that would break `pytest.raises(..., match=...)` (a `re.search`); no unbalanced brackets, no `.` in the matched substring.
- **`xfail(strict=True)` self-destruct is correct.** Today the assertion fails → XFAIL → suite exit code stays 0 (green now, as the roadmap requires). Once 2.2's fix lands, the test passes → XPASS → `strict=True` reports it as a *failure*, mechanically forcing 2.2 to remove the marker. This is the right primitive for "stays RED until 2.2" without breaking CI in the interim.
- **Candidate-selection ordering holds for every Task-4 case.** Partial-install (`v20.1.0` skipped → `v18.0.0` returned) and non-dir tolerance (`somefile` alongside `v18.0.0`) both resolve to `v18.0.0` under the current reverse-lexicographic iteration, so these are correctly green against today's code.
- **`_CLAUDE_BIN` reset is legitimately omitted.** The roadmap line mentions resetting `agents._CLAUDE_BIN`, but per spec note 19 (§ Instantiation gotcha) that reset is only required for tests that route through `_run_claude`. Every planned test calls `_resolve_claude()` directly, which never reads or writes the cache, so no reset is needed. The omission is correct, not an oversight — the plan could have stated the reasoning inline, but the behavior is right.

### Positive Notes
- Tightly scoped: test-only, single file, no product code, no migrations, no security surface.
- Phased ordering (scaffold → green → RED) with a two-commit plan that keeps each commit's suite green is clean and reviewable.
- The `_make_claude_bin` helper isolates the one non-obvious construction detail (`bin/claude` only needs to exist, content irrelevant) per the spec.
- Correctly distinguishes the milestone contract from the stale spec case #47 and documents the override rather than silently diverging.

The plan is solid, faithful to both the roadmap contract and the spec note, and every ordering claim checks out against the actual sort behavior.

PLAN_REVIEW_PASS
