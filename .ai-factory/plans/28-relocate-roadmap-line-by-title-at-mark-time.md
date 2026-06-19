# Plan: Relocate roadmap line by title at mark time

## Context
Make `mark_done` / `mark_skipped` re-locate the target milestone line by title at edit time instead of trusting the parse-time `line_number`, so concurrent edits to `ROADMAP.md` can't flip the wrong checkbox.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Line relocation helper

- [x] **Task 1: Add `_find_milestone_line` helper**
  Files: `orchestrator/roadmap.py`
  Add a module-level function `_find_milestone_line(lines: list[str], milestone: Milestone) -> int | None`. Iterate `lines` with `enumerate`; for each line apply `CHECKBOX_RE.match(line.strip())` (mirror `parse_roadmap`, which strips before matching). Return the index `i` of the first line where the regex matches, group 1 equals `" "` (unchecked state), and `m.group(2).strip() == milestone.title`. Return `None` when no match is found. Place it near the other module-level functions, after `parse_roadmap`.

### Phase 2: Wire helper into mark functions

- [x] **Task 2: Resolve index via helper in `mark_done`** (depends on Task 1)
  Files: `orchestrator/roadmap.py`
  In `mark_done`, after reading `lines`, compute `idx = _find_milestone_line(lines, milestone)` and fall back to `idx = milestone.line_number` when it returns `None`. Replace both uses of `milestone.line_number` (the read `lines[milestone.line_number]` and the write `lines[milestone.line_number] = new_line`) with `idx`. Keep the function signature and the elapsed-time formatting unchanged.

- [x] **Task 3: Resolve index via helper in `mark_skipped`** (depends on Task 1)
  Files: `orchestrator/roadmap.py`
  In `mark_skipped`, apply the same pattern: `idx = _find_milestone_line(lines, milestone)` with fallback to `milestone.line_number` when `None`, then operate on `lines[idx]` for both the read and the write. Keep the signature and the `⚠️ SKIPPED` replacement text unchanged.
