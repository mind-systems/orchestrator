## Plan Review Summary

**Plan:** `27-next-number-tests.md` — unit tests for `_next_number`
**Files Reviewed:** plan + governing spec (`.ai-factory/specs/19-next-number.md`) + roadmap contract line (`ROADMAP_TESTS.md`, `## main.py`) + target `orchestrator/main.py:84-93` + `tests/test_main.py` + prior review (`27-...-plan-review-1.md`)
**Risk Level:** 🟢 Low

This is a re-review. Plan v2 resolves all three findings from plan-review-1.

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): the plan adds only test functions to `tests/test_main.py` — no module boundary or dependency impact. OK.
- **Rules** (`.ai-factory/RULES.md`): absent — skipped.
- **Roadmap** (`ROADMAP_TESTS.md`): the milestone line resolves under `## main.py` — `- [ ] **`_next_number` tests**`, `Spec: .ai-factory/specs/19-next-number.md`. Target file, function, and risk framing all match. Alignment OK.

### Verification against ground truth

I re-derived every asserted value from the actual function (`existing = sorted(directory.glob("*.md"))`, reversed scan for the first digit-prefixed stem, `len(existing)+1` fallback). **All nine assertions are correct:**
- empty → 1; `03-x.md` → 4; `01/02/05` → 6 (max+1, not count+1)
- `01-a`+`zz-notes` → 2; `aa-notes`+`02-b` → 3 (`sorted` gives `["02-b.md","aa-notes.md"]`, reversed skips `aa`); `notes`+`readme` → 3 (fallback)
- `08/09` → 10; `10-c` → 11; `9-a`+`10-b` → 10 (string sort `["10-b.md","9-a.md"]`, reversed visits `9-a` first → `int("9")+1`)

The `tmp_path` + real-file approach and `from orchestrator.main import _next_number` import are both correct — the function still lives in `main.py`. `grep` confirms no existing `_next_number` coverage in `tests/test_main.py`, so no duplication.

### Resolution of prior-review findings

1. **Spec-contradiction on the characterization test — resolved.** Task 3 case 3 now carries an explicit `DEVIATION` annotation. I verified its claim directly against the roadmap contract line, which reads: *"add a case documenting that a mixed-width `['9-a.md','10-b.md']` set sorts `10` before `9` as strings ... so a future change that drops padding trips a test."* The contract line **does** direct this exact case with these exact filenames and frames it as a characterization pin. Per the governing chain, the contract line supersedes the spec's softer "record as a note" guidance, and the plan documents this rather than overriding silently. This is a grounded, correct deviation — conformance, not a defect. The annotation also correctly surfaces the *reachable* form (`99`/`100`, live once counts cross 99) as out-of-scope for a test-only milestone and points to the prior review's deferred observation.

2. **Two dropped spec cases — restored.** `aa-notes.md`+`02-b.md` → 3 is now Task 2 case 2 (with the intended lexicographic-complement rationale), and `10-c.md` → 11 is now Task 3 case 2.

3. **Test Command — aligned.** Now `uv run pytest tests/ -v`, matching the established full-suite convention.

### Critical Issues
None.

### Positive Notes
- Every asserted value is arithmetically correct against the real function — no fantasy values, no off-by-one.
- The characterization test is now both grounded in the governing contract and clearly labelled (name + comment marking the asserted `10` as characterizing broken, non-padded behavior).
- Branch coverage is complete: empty, single, gapped-max, both lexicographic placements of a stray non-digit stem, all-non-digit fallback, zero-padded rollover, double-digit sole entry, and the mixed-width sort boundary.
- Setup notes are concrete and grounded ("no mocking — the function reads the real directory through `Path.glob`"), matching the spec's fully-pure-over-real-filesystem characterization.

PLAN_REVIEW_PASS
