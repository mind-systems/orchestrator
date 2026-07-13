## Code Review Summary

**Files Reviewed:** 1 plan (`plans/24-2-2-...md`) against ground truth: `orchestrator/agents.py`, `tests/test_agents.py`, `.ai-factory/specs/20-resolve-claude-semver-fix.md`, `.ai-factory/specs/19-resolve-claude-cli.md`, `ROADMAP.md`
**Risk Level:** 🟡 Medium

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): OK. The change is confined to the `_resolve_claude` resolver internals in `agents.py`; the new pure helper introduces no cross-module edge, no dependency (the spec's zero-dep constraint is honored — no `packaging`), and does not touch the file protocol. No boundary violation.
- **Rules** (`.ai-factory/RULES.md`): absent — WARN, non-blocking. No explicit convention file to check against.
- **Roadmap linkage**: OK. Milestone 2.2 exists at `ROADMAP.md:81` and its `Spec:` tag resolves to `.ai-factory/specs/20-resolve-claude-semver-fix.md`, which in turn references `19-resolve-claude-cli.md`. Both were read; findings below are judged against that tree.
- **skill-context** (`aif-review/SKILL.md`): absent — no project-specific review overrides.

### Critical Issues
None. The core design is correct: the ordering claims are verified against ground truth — `_resolve_claude` sits at `agents.py:81`, the buggy loop `for node_dir in sorted(nvm_base.iterdir(), reverse=True):` is at line 89, and the strict-xfail decorator is at `tests/test_agents.py:259-262`. The composite-key ordering (`(1, version_tuple)` parseable vs `(0,)`-tier unparseable) preserves every existing green case: `multi_candidate_returns_highest` (v20.1.0 > v18.0.0), `partial_install_skipped`, `non_dir_entry_tolerated`, and the not-found raises all still hold under the new order, and the RED ordering case (v20.11.0 > v9.0.0) flips green. The deviation note correctly justifies why the strict-xfail removal is mandatory (an XPASS under `strict=True` is reported as a suite failure), so "touch agents.py only" cannot be met literally.

### Findings

1. **Missing step — the spec's direct unit cases for `_sorted_nvm_node_dirs` are neither planned nor reconciled.**
   `specs/20-resolve-claude-semver-fix.md:30` states: *"The pure `_sorted_nvm_node_dirs` also gets direct unit cases (single- vs double-digit majors, unparseable-sorts-last, empty list) — no monkeypatching needed since it takes plain `Path`s."* The plan adds none of these — Task 2 only deletes the xfail decorator. The spec attributes these cases to 2.1, but 2.1 was authored RED *before this helper existed*, and the current `tests/test_agents.py` contains no direct helper-level test — so no task actually owns them and the coverage the spec calls for does not exist. Two of the three (`empty list → []`, `unparseable-sorts-last` at the helper level) are the never-raise / total-ordering contract clauses the whole milestone exists to guarantee, and they are exactly silent-failure surfaces (wrong order, no crash) that the test-philosophy discriminator says to cover. The plan should either add these direct unit cases against `_sorted_nvm_node_dirs` in `tests/test_agents.py` (the file it is already editing), or state explicitly in the deviation note that it consciously relies on the existing `_resolve_claude`-level coverage and skips them — right now it is silent on a governing-spec requirement.

2. **Stale docstring/comment left behind in the edited test file.**
   `test_resolve_claude_non_dir_entry_tolerated` (`tests/test_agents.py:240-251`) documents obsolete mechanics once the fix lands: the docstring says the stray file *"sorting ahead of the valid version dir under reverse=True is visited first"*, and the inline comment at line 247 reads `# sorts before v18.0.0 under reverse=True`. After the change, an unparseable name (`zzstray`) sorts **last**, not ahead of `v18.0.0` — so it is visited last. The assertion still passes (v18 is still returned), but the stated reasoning is now false. Since Task 2 edits this exact file, this is a finding, not a deferred observation: the plan should include correcting these two lines (they cost nothing and the milestone's own change is what makes them wrong). As written, Task 2's "Change nothing else in the file" instruction locks the staleness in.

3. **Low — `str.isdigit()` as the guard for `int()` can violate the "never raise on any input" contract.**
   Both the plan (Task 1) and `specs/20-...md:15` prescribe *"the leading run of all-integer (`str.isdigit()`) segments into an int tuple."* `str.isdigit()` returns `True` for Unicode numeric forms that `int()` cannot parse (e.g. superscript `"²".isdigit()` is `True` but `int("²")` raises `ValueError`), so a segment like that would break the explicit *"must never raise on any input"* contract (plan Task 1; spec "Guards / edge cases"). In practice nvm directory names are ASCII, so this never bites — hence low severity — but to honor the contract strictly the implementer should use `str.isdecimal()` (or wrap the `int()` in try/except) rather than `str.isdigit()`. Worth a one-word steer in the plan given the contract is stated so emphatically.

### Positive Notes
- Ground-truth line references (`agents.py:81`, the exact loop, `test_agents.py:259-262`) are all accurate — no drift between the plan and the files.
- The deviation note is exemplary: it names the ground-truth conflict (strict xfail → XPASS → suite failure), explains why "agents.py only" cannot hold, and scopes the test-file edit to the single mandatory line.
- Zero-dependency and byte-identical-branch constraints from the spec (PATH-hit early return, `is_dir()` guard, `FileNotFoundError` message, `_CLAUDE_BIN` cache, no new imports) are all explicitly preserved.
- The composite-key design with a parseable/unparseable discriminator correctly avoids the cross-type comparison trap (an int-tuple is never compared against a string because the leading tier always differs first).

The plan is fundamentally sound and the fix will work, but findings 1 and 2 leave a spec-mandated test surface unowned and a stale comment baked into an edited file — both fixable within the milestone's boundary. Withholding pass so they are addressed or explicitly reconciled.
