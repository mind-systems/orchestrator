# Code Review: Relocate roadmap line by title at mark time

**Scope:** `orchestrator/roadmap.py` (only code file changed; remaining staged changes are `.ai-factory/` docs/notes/plans).

## What the change does
Adds `_find_milestone_line(lines, milestone)` and wires it into `mark_done` and `mark_skipped`. The index used for both the read and the write is now resolved by title match at edit time, falling back to the frozen `milestone.line_number` only when no unchecked title match is found. Signatures unchanged; `main.py` callers untouched.

## Correctness analysis

- **Matches `parse_roadmap` semantics.** The helper applies `CHECKBOX_RE.match(line.strip())` exactly as the parser does, so any line the parser would treat as a milestone is locatable here. ✔
- **Unchecked guard is correct.** `m.group(1) == " "` ensures an already-marked duplicate-title line is never re-hit, and "first match" aligns with the `pending[0]` selection strategy described in the spec. ✔
- **`replace` target is safe on the unstripped line.** `_find_milestone_line` matches against `line.strip()`, but `mark_done`/`mark_skipped` call `line.replace("- [ ]", ...)` on the original unstripped `lines[idx]`. Since `CHECKBOX_RE` anchors `^- \[` on the stripped form, the matched line contains the literal substring `- [ ]`; `replace(..., 1)` flips it regardless of leading whitespace. ✔
- **Both read and write use the same `idx`.** No chance of reading one line and writing another. ✔
- **STOP marker not honored by the helper, but harmless.** `_find_milestone_line` scans the whole file including lines after `---STOP---`. A milestone passed to `mark_done` was selected from `pending` (unchecked, before the marker), so its first unchecked occurrence is found before reaching any post-marker line. No mis-target. ✔
- **Fallback preserves prior behavior.** When the title is absent (renamed/removed), `idx = milestone.line_number` reproduces the original code path exactly — no regression for the unedited-file case. ✔

## Non-blocking observation
The fallback path (`idx = milestone.line_number`) retains the pre-existing risk of an `IndexError` if `ROADMAP.md` was edited such that the title is no longer found *and* the file shrank below the stored index. This is unchanged from the original implementation and is explicitly the documented fallback behavior ("keeps current behavior if title not found"); the common path is now strictly safer than before. Not a defect introduced by this change — noted only for awareness should the dynamic re-scan loop (note 15) ever drive marking against a heavily-mutated file.

## Verdict
The change is correct, minimal, and faithful to the plan and spec. No bugs, no security issues, no type/runtime concerns.

REVIEW_PASS
