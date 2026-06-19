# Relocate roadmap line by title at mark time

**Date:** 2026-06-19
**Source:** conversation context

## Key Findings

- `mark_done` / `mark_skipped` in `roadmap.py` write to `milestone.line_number` directly — a line index frozen at parse time in `parse_roadmap`. The line is never re-located before editing.
- This is a latent mis-mark bug: if any agent edits `ROADMAP.md` between parse and the final `mark_done` (e.g. inserts lines above the milestone), `line_number` is stale and the checkbox is flipped on the wrong line.
- The fix is root-cause, not defensive: re-locate the target line by matching `CHECKBOX_RE`, an unchecked box `[ ]`, and `title == milestone.title` at edit time. Fall back to the stored `line_number` only if no match is found.
- This fix is a prerequisite for the dynamic re-scan loop (note 15): with re-scan, a mis-mark that leaves the checkbox un-flipped would cause the same milestone to be re-selected forever. Correct marking guarantees termination.

## Details

### Current state (`orchestrator/roadmap.py`)

```python
def mark_done(path, milestone, elapsed_secs=None):
    lines = path.read_text().splitlines()
    line = lines[milestone.line_number]          # ← trusts frozen index
    new_line = line.replace("- [ ]", "- [x]", 1)
    ...

def mark_skipped(path, milestone):
    lines = path.read_text().splitlines()
    line = lines[milestone.line_number]          # ← same
    lines[milestone.line_number] = line.replace("- [ ]", "- [x] ⚠️ SKIPPED (already implemented)", 1)
    ...
```

`CHECKBOX_RE = re.compile(r"^- \[([ x])\] \*\*(.+?)\*\*\s*[—–-]\s*(.+)$")` already captures the title in group 2.

### Target change

Add a module-level helper that finds the milestone's current line index:

```python
def _find_milestone_line(lines: list[str], milestone: Milestone) -> int | None:
    """Return the index of the first UNCHECKED line whose title matches, or None."""
    for i, line in enumerate(lines):
        m = CHECKBOX_RE.match(line.strip())
        if m and m.group(1) == " " and m.group(2).strip() == milestone.title:
            return i
    return None
```

Both `mark_done` and `mark_skipped` resolve the index via:

```python
idx = _find_milestone_line(lines, milestone)
if idx is None:
    idx = milestone.line_number   # fallback — keeps current behavior if title not found
```

then operate on `lines[idx]`.

### Why "first unchecked with this title" is correct

The dynamic loop (note 15) always selects `pending[0]` — the first unchecked milestone top-to-bottom. If two milestones share a title, `pending[0]` is the topmost unchecked one, which is exactly what `_find_milestone_line` returns. The selection and the marking agree by construction.

### Guards

- Match against `line.strip()` to mirror how `parse_roadmap` matches (it strips before applying `CHECKBOX_RE`).
- Require the unchecked state `m.group(1) == " "` so an already-marked duplicate title isn't re-hit.
- Keep the `line_number` fallback so behavior is unchanged when the title can't be located (no regression for callers that pass a milestone parsed from the same unedited file).

### Scope

`orchestrator/roadmap.py` only. No signature changes — `mark_done(path, milestone, elapsed_secs)` and `mark_skipped(path, milestone)` keep their current parameters. Callers in `main.py` are untouched.

### Verify

- Parse a roadmap, insert a line above a pending milestone in the file, then call `mark_done` for that milestone — assert the correct (title-matched) line is flipped, not the shifted index.
- A milestone whose title is absent (simulating an edit that renamed it) falls back to `line_number` and still writes without raising.

## Open Questions

None — optionally tighten the match to also compare `description` (group 3) if duplicate titles with different descriptions ever appear; not needed for current roadmaps.
