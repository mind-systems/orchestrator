# Test Plan: `parse_roadmap` + roadmap helpers unit tests

## Context
Unit-test the ROADMAP.md parser and updater in `orchestrator/roadmap.py`: `parse_roadmap`, `Milestone.slug`, `_find_milestone_line`, `mark_done`, and `mark_skipped`. These functions read/write milestone checkbox lines and drive the orchestrator loop, so their parsing and file-mutation behavior must be locked down.

## Settings
- Testing: yes
- Logging: minimal
- Docs: no

## Test Command
`uv run pytest tests/test_roadmap.py`

## Target Spec File
`tests/test_roadmap.py`

## Notes for the implementer
- Test style mirrors `tests/test_main.py`: module-level `def test_*` functions (no classes), one-line docstring stating the behavior, `tmp_path` fixture for file I/O.
- Imports: `from orchestrator.roadmap import parse_roadmap, Milestone, _find_milestone_line, mark_done, mark_skipped`.
- To build a roadmap file, write lines joined by `"\n"` to a `tmp_path / "ROADMAP.md"` file and pass the `Path` in.
- Milestone separator accepts em dash `—`, en dash `–`, or ASCII hyphen `-` (`roadmap.py:9`). Use real Unicode dash characters in test data.
- `mark_done`/`mark_skipped` write the file back as `"\n".join(lines) + "\n"` — assert on the resulting line content via `read_text().splitlines()`.

## Tasks

### Phase 1: parse_roadmap — milestone collection & sections

- [x] **Task 1: `parse_roadmap` milestone collection and done flags**
  Files: `tests/test_roadmap.py`
  Test cases:
  - `should set done=True for [x] lines and done=False for [ ] lines when the file mixes both` (case 1)
  - `should not collect a line that has no **title** checkbox pattern` (case 5 — e.g. a plain bullet or prose line is skipped)
  - `should record the 0-based line_number for each parsed milestone matching its position in the file`

- [x] **Task 2: `parse_roadmap` section assignment**
  Files: `tests/test_roadmap.py`
  Test cases:
  - `should set section="Phase name" on milestones that follow a "## Phase name" heading` (case 4)
  - `should also assign section from a "### Subheading" heading` (heading match covers `## ` and `### `, `roadmap.py:50`)
  - `should leave section=None on milestones that appear before any heading`

### Phase 2: parse_roadmap — `---STOP---` breakpoint

- [x] **Task 3: `parse_roadmap` breakpoint behavior**
  Files: `tests/test_roadmap.py`
  Test cases:
  - `should set breakpoint_hit=True and exclude milestones after the marker when ---STOP--- is followed by milestone lines` (case 2 — also assert collected `milestones` only contains the pre-marker ones)
  - `should set milestones_after_breakpoint to the count of milestone lines following the marker` (case 2)
  - `should set breakpoint_hit=False when ---STOP--- is the last non-blank line with nothing after it` (case 3)
  - `should set breakpoint_hit=False and milestones_after_breakpoint=0 when no ---STOP--- marker is present`

### Phase 3: Milestone.slug

- [x] **Task 4: `Milestone.slug` generation**
  Files: `tests/test_roadmap.py`
  Test cases:
  - `should produce "config-file-replace-env-vars" when title is "Config file — replace env vars"` (case 6 — em dash and spaces collapse to single hyphens, lowercased)
  - `should preserve digits and produce "oauth2-setup" when title is "OAuth2 setup"` (case 7)
  - `should strip leading and trailing hyphens from the slug` (e.g. a title with surrounding punctuation)

### Phase 4: _find_milestone_line

- [x] **Task 5: `_find_milestone_line` lookup**
  Files: `tests/test_roadmap.py`
  Test cases:
  - `should return the correct 0-based index when an unchecked [ ] line matches the milestone title exactly` (case 8)
  - `should return None when a line with the same title is already checked [x]` (case 9 — only `[ ]` lines match)
  - `should return None when no line with that title is present` (case 10)

### Phase 5: mark_done / mark_skipped

- [x] **Task 6: `mark_done` line mutation**
  Files: `tests/test_roadmap.py`
  Test cases:
  - `should replace "- [ ]" with "- [x]" on the matching line when called without elapsed_secs`
  - `should append " [2m 5s]" after converting the checkbox when elapsed_secs is 125` (case 11)
  - `should format elapsed as "{hours}h {mins}m {secs}s" when elapsed_secs exceeds one hour` (e.g. 3725 → `1h 2m 5s`, `roadmap.py:97`)
  - `should locate the line via _find_milestone_line and mark line 3 when milestone.line_number is a stale 0 but the title sits on line 3` (case 13)
  - `should leave other lines in the file unchanged after marking one milestone done`

- [x] **Task 7: `mark_skipped` line mutation**
  Files: `tests/test_roadmap.py`
  Test cases:
  - `should replace "- [ ]" with "- [x] ⚠️ SKIPPED (already implemented)" preserving the rest of the line` (case 12 — assert the trailing `— ...` description survives)
  - `should mark the title-matched line even when milestone.line_number is stale, resolving via _find_milestone_line`
