## Code Review Summary

**Files Reviewed:** 1 plan (`plans/24-2-2-...md`) against ground truth: `orchestrator/agents.py`, `tests/test_agents.py`, `.ai-factory/specs/20-resolve-claude-semver-fix.md`, `.ai-factory/ROADMAP.md:81`, and the prior `plan-review-1`.
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): OK. The change is confined to the `_resolve_claude` resolver internals plus a new module-level pure helper in `agents.py`; no cross-module edge, no dependency (zero-dep constraint honored — no `packaging`), no touch to the file protocol. No boundary violation.
- **Rules** (`.ai-factory/RULES.md`): absent — WARN, non-blocking.
- **Roadmap linkage**: OK. Milestone 2.2 at `ROADMAP.md:81`; its `Spec:` tag resolves to `.ai-factory/specs/20-resolve-claude-semver-fix.md`, which references `19-resolve-claude-cli.md`. Findings judged against that tree.
- **skill-context** (`aif-review/SKILL.md`): absent — no project-specific overrides.

### Critical Issues
None.

### Resolution of plan-review-1 findings
This is round 2. All three prior findings are now addressed, each grounded in ground truth:

1. **Missing helper unit cases → resolved.** Task 2 edit 3 now adds direct `agents._sorted_nvm_node_dirs` unit cases (single- vs double-digit majors, unparseable-sorts-last, empty list), and the "Assumptions / deviation note" consciously reconciles why this task owns them (2.1 was authored RED before the helper existed; no task currently owns the spec's `20-...md:30` helper-level cases). This fulfills the governing spec rather than silently skipping it.
2. **Stale docstring/comment → resolved.** Task 2 edit 2 explicitly corrects both the `test_resolve_claude_non_dir_entry_tolerated` docstring and the inline comment at `tests/test_agents.py:247` (`# sorts before v18.0.0 under reverse=True`), noting the stray name now sorts **last**, while keeping the assertion (v18 still returned).
3. **`str.isdigit()` never-raise hazard → resolved.** Task 1 now prescribes `str.isdecimal()` with a correct rationale (`"²".isdigit()` is `True` but `int("²")` raises), and offers try/except as an equivalent. This honors the "never raise on any input" contract from spec "Guards / edge cases".

### Verification of the design
- Line references are accurate: `_resolve_claude` at `agents.py:81`, the buggy loop `for node_dir in sorted(nvm_base.iterdir(), reverse=True):` at line 89, the strict-xfail decorator at `tests/test_agents.py:259-262`, `test_resolve_claude_non_dir_entry_tolerated` at 240-251.
- Composite-key ordering (`(1, version_tuple)` parseable vs `(0,)`-tier unparseable with `reverse=True`) is sound and preserves every existing green case (`multi_candidate_returns_highest`, `partial_install_skipped`, `non_dir_entry_tolerated`, the not-found raises) while flipping the RED ordering case (v20.11.0 > v9.0.0) green.
- The cross-type comparison trap is correctly avoided: the leading tier discriminator (0 vs 1) always differs first, so an int-tuple is never compared against a string. The plan calls this out explicitly.
- Leading-decimal-run parse (`v18.20.4` → `(18,20,4)`; `system`/`lts`/`zzstray` → unparseable bucket) handles malformed/trailing-non-integer segments without raising, satisfying the total-ordering + never-raise contract.
- Deviation note correctly justifies the mandatory strict-xfail removal (an XPASS under `strict=True` is a suite failure), so "touch agents.py only" cannot hold literally — a correct, spec-grounded deviation.
- Zero-dep and byte-identical-branch constraints (PATH-hit early return, `is_dir()` guard, `FileNotFoundError` message, `_CLAUDE_BIN` cache, no new imports) are all explicitly preserved.

### Positive Notes
- The revision closes every prior finding without over-correcting: the fix stays confined to the two named files, the assertion bodies are left intact, and the test edits are scoped precisely.
- The "Assumptions / deviation note" is exemplary — it names each ground-truth conflict, cites the exact xfail/strict mechanics, and attributes the helper unit cases to the governing spec.
- Task 2 edit 3's prose ("among two unparseable names they order by string") correctly steers the implementer to include a second unparseable name so the string-ordering-among-unparseables clause from spec `20-...md:16` is actually exercised, even though the illustrative list is prefixed "a mix like".

The plan is solid, fully grounded, and resolves all outstanding findings.

PLAN_REVIEW_PASS
