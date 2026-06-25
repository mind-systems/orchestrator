# Test Coverage Plan

**Date:** 2026-06-25
**Source:** roadmap-test-coverage inline analysis

## Source Overview

Orchestrator is a pure Python CLI tool (~1400 LOC across 6 files) with no test suite.
The pipeline drives Claude agents via subprocess and gates pass/fail on string signals
written to files. The most dangerous failure mode is silent wrong behavior: a regex
returning None instead of a percentage, a resume step detection returning the wrong
phase, or a signal check returning True on a false positive — all proceed quietly
while the pipeline does the wrong thing.

## Silent-Failure Areas

### 1. `_has_signal(text, signal)` — `agents.py:42`

Determines whether a review file contains REVIEW_PASS or PLAN_REVIEW_PASS.
A wrong True → pipeline commits bad code. A wrong False → pipeline loops forever.
Pure string logic, zero dependencies, trivial to unit test.

**Test cases:**
- exact match as the last line → True
- exact match as line 3 of 5 (within last-5 window) → True
- signal is a substring of a longer word ("no REVIEW_PASS here") → False
- signal with trailing whitespace in file → True (`.strip()` already handles)
- empty text → False
- signal appears only in line 6 of a 10-line file → False (outside last-5)
- exact match with `PLAN_REVIEW_PASS` → True

### 2. `_parse_pct(text, pattern)` — `main.py:30`

Usage guard regex. Returns None silently → guard disabled → orchestrator
proceeds past quota. Pure regex, no dependencies.

**Test cases:**
- `"Current session: 85%"` with session pattern → 85.0
- `"Current week (all models): 42.5%"` with weekly pattern → 42.5
- no match in text → None
- text with multiple numbers, only pattern match counts → correct number
- malformed (e.g. `"session: abc%"`) → None

### 3. `_validate_sidecar_step(...)` — `main.py:108`

Validates that a sidecar `step` value still has its referenced artifact on disk.
Wrong return → resume starts at wrong step → overwrites or skips work.
Logic is pure (path.exists() checks), needs a tmp_path but no subprocess.

**Test cases:**
- empty string → ""
- `"planned"` / `"implemented"` → always valid, returned as-is
- `"plan_review_failed:2"` with plan-review-2.md present → valid
- `"plan_review_failed:2"` with plan-review-2.md missing → ""
- `"plan_reviewed"` with a file ending `PLAN_REVIEW_PASS` present → valid
- `"plan_reviewed"` with no passing file → ""
- `"review_failed:1"` with review-1.md present → valid
- `"review_failed:1"` with review-1.md missing → ""
- malformed `"plan_review_failed:abc"` → ""
- unrecognized value → returned as-is

### 4. `_detect_milestone_step` / `_detect_test_milestone_step` — `main.py:157,419`

Resume detection: determines where a previous run left off. Wrong step →
runs wrong phase, potentially overwriting review artifacts or skipping implementation.
Calls `subprocess.run(["git", ...])` → needs `tmp_path` + `git init`.

**Test cases (implement mode):**
- no plan file → `("plan", 1, plan_path)`
- plan exists, sidecar step="planned" → `("plan_review", 1, plan_path)`
- sidecar step="plan_reviewed", no git changes → `("implement", 1, plan_path)`
- sidecar step="implemented", no review files → `("review", 1, plan_path)`
- sidecar step="review_failed:1", review-1.md exists → `("implement", 2, plan_path)`
- sidecar step="review_failed:2" at max, then artifact deleted → falls through to heuristic
- slug mismatch: plan written as `01-slug.md`, caller passes `seq=02` → canonical resolved to `01`
- sidecar step="done" (hypothetical unrecognized) → falls to heuristic

**Test cases (test mode):**
- mirrors implement mode but uses test-runs/ and `test_run_failed:` prefix

### 5. `_extract_test_command(plan_path)` — `agents.py:434`

Parses `## Test Command` section from a plan file. Returns None silently →
TestRunner logs error and returns False without running anything.
Pure string logic, needs a tmp file.

**Test cases:**
- section with backtick-wrapped command → command without backticks
- section with bare command (no backticks) → command string
- no `## Test Command` section → None
- section with blank body before another `##` → None
- command is the first non-empty line after the heading

### 6. `parse_roadmap` + `Milestone.slug` + `_find_milestone_line` — `roadmap.py`

Wrong parse → wrong milestones processed. Wrong slug → all artifact filenames wrong
→ resume fails silently (falls to "plan" each time). Wrong `_find_milestone_line` →
marks wrong line as done → double-processing.
File I/O only, needs tmp file, no subprocess.

**Test cases (parse_roadmap):**
- mixed done/pending milestones → correct done flags
- `---STOP---` with milestones after → breakpoint_hit=True, after-count correct
- `---STOP---` at end of file (nothing after) → breakpoint_hit=False
- section headings (`##`, `###`) assigned to subsequent milestones
- malformed lines (no `**`) → skipped
- em dash / en dash / hyphen variants in separator → all parsed

**Test cases (Milestone.slug):**
- `"Config file — replace env vars"` → `"config-file-replace-env-vars"`
- title with numbers and mixed case → lowercase, digits preserved
- leading/trailing separators stripped

**Test cases (_find_milestone_line):**
- unchecked line matching title → correct index
- checked line with same title → not returned (must be unchecked)
- title not present → None
- multiple unchecked lines, first match returned

## Testability Blockers

1. **`_CLAUDE_BIN = _resolve_claude()` at import** (`agents.py:94`) — module fails to
   import without `claude` installed. Must be made lazy before any test in
   `tests/test_agents.py` can run. Fix: cache as `_CLAUDE_BIN: str | None = None`,
   resolve inside `_run_claude()`.

2. **`subprocess.run(["git", ...])` inline in `_detect_milestone_step`** — tests must
   create a real git repo in `tmp_path` via `git init && git commit --allow-empty`.
   No patching needed; the git calls are correct, the test just needs an initialized repo.

3. **`_with_caffeinate` crashes on Linux** — `FileNotFoundError` on `caffeinate` Popen.
   Fix: wrap with `try/except FileNotFoundError` or check `sys.platform`.

## Refactor Required (testability)

Both lazy `_CLAUDE_BIN` and `_with_caffeinate` non-crash are preconditions for
importing agents.py and main.py cleanly in tests. These must land in ROADMAP.md
before ROADMAP_TESTS.md milestones are implemented.
