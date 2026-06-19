## Plan Review Summary

**Files Reviewed:** plan + `orchestrator/roadmap.py`, `orchestrator/main.py` (callers), notes 14/15
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): WARN — no boundary impact. Change is contained to `orchestrator/roadmap.py`, the same module that already owns parse/mark logic. No new cross-module dependencies introduced.
- **Rules** (`.ai-factory/RULES.md`): absent — gate skipped (WARN, non-blocking).
- **Roadmap** (`.ai-factory/ROADMAP.md` present): OK — this is a `fix` (latent mis-mark bug). The roadmap already carries this milestone (working tree shows it added) and note 14 documents the linkage. Acceptable.
- **Skill-context** (`.ai-factory/skill-context/aif-review/SKILL.md`): absent — no project overrides to apply.

### Critical Issues
None.

### Correctness Verification
The plan matches the codebase precisely:
- `CHECKBOX_RE = r"^- \[([ x])\] \*\*(.+?)\*\*\s*[—–-]\s*(.+)$"` — group 1 is the single state char (`" "`/`"x"`), group 2 is the title. The plan's checks (`m.group(1) == " "`, `m.group(2).strip() == milestone.title`) are correct against this regex.
- `parse_roadmap` matches on `line.strip()` (line 49/62); the plan mirrors this with `CHECKBOX_RE.match(line.strip())` — consistent stripping, no mismatch risk.
- `milestone.title` is already `.strip()`-ed at parse time (line 65), and the helper re-strips group 2, so comparison is symmetric.
- Both `lines[milestone.line_number]` reads/writes in `mark_done` (lines 76, 83) and `mark_skipped` (lines 90, 91) are correctly identified for replacement with `idx`.
- The `line_number` fallback preserves current behavior when the title is absent — no regression for callers in `main.py`, which still pass `milestone.line_number` only to the planner/implementer agents (lines 300/360/etc.), not to the mark functions. Signatures unchanged, so callers stay untouched as claimed.

### Non-blocking Observations
- **First-unchecked semantics is correct.** `_find_milestone_line` returns the topmost unchecked title match. Since the dynamic loop (note 15) selects `pending[0]`, selection and marking agree by construction. Duplicate titles are handled safely.
- **STOP-marker interaction is benign.** The helper scans the whole file and is unaware of `---STOP---`. In theory it could match a same-title unchecked line below the marker, but the marked milestone always comes from *before* the marker and is itself unchecked at mark time, so the helper hits the correct (earlier) line first. No action needed.
- **Logging:** plan declares "minimal" logging; the silent fallback path swallows the "title not found" case. Given the fix's role as a prerequisite for the re-scan loop (note 15), a single debug/warn log on fallback would aid future diagnosis — optional, not required by this plan's scope.

### Positive Notes
- Root-cause fix, not a defensive patch — relocates by identity (title + unchecked state) rather than trusting a frozen index.
- Clean phasing: helper first, then wiring; Task 2/3 correctly declare dependency on Task 1.
- Scope is tight and accurately bounded to one module; no migrations, no signature/API changes, no caller churn.
- File paths and API usage are all correct against the actual source.

PLAN_REVIEW_PASS
