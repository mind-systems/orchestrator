## Plan Review Summary

**Plan:** `27-next-number-tests.md` — unit tests for `_next_number`
**Files Reviewed:** plan + governing spec (`.ai-factory/specs/19-next-number.md`) + target `orchestrator/main.py:84-93` + `tests/test_main.py`
**Risk Level:** 🟡 Medium

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): no boundary/dependency impact — the plan only adds test functions to `tests/test_main.py`. No WARN.
- **Rules** (`.ai-factory/RULES.md`): absent — skipped.
- **Roadmap** (`ROADMAP_TESTS.md`): the milestone line resolves — `- [ ] **`_next_number` tests**` under `## main.py`, `Spec: .ai-factory/specs/19-next-number.md`. The plan's target file, function, and risk framing all match the roadmap line. Alignment OK.

I verified every test-case value in the plan against the actual code (`existing = sorted(directory.glob("*.md"))`, reversed scan for the first digit-prefixed stem, `len(existing)+1` fallback). **All asserted return values are correct** — empty→1, `03-x`→4, `01/02/05`→6, `01-a`+`zz-notes`→2, `notes`+`readme`→3, `08/09`→10, and the `9-a`/`10-b`→10 characterization value all match the code exactly. The `tmp_path` + real-file approach and the `from orchestrator.main import _next_number` import are both correct (the function still lives in `main.py`, unlike the `_detect_*`/`_validate_*` helpers that moved to `orchestrator.resume`).

### Critical Issues

**1. Task 3 case 2 directly contradicts the governing spec's explicit recommendation.**
The spec's Gotchas section addresses exactly this scenario and concludes:
> "Worth a note for whoever owns artifact numbering next, **rather than a test asserting the (currently unreachable at low milestone counts) broken behavior as correct**."

The plan does the opposite — Task 3 case 2 is precisely such a characterization test pinning the broken value (`10`) as correct. Two sub-problems compound it:
  - The plan uses `9-a.md`/`10-b.md` (single- vs double-digit). Given the only caller formats the seq as `:02d` (`main.py`), a single-digit `9-a.md` stem is **never produced in practice** — so this input models a scenario the production code cannot currently reach. The spec instead identifies the *reachable* boundary as `99`/`100` (milestone 100 emits `"100-slug.md"` beside `"99-slug.md"`), which is where the latent lexicographic bug actually becomes live.
  - Reconcile before implementing: either follow the spec (drop the characterization test, record the latent-boundary observation as a note for the artifact-numbering owner), or, if a regression pin is genuinely wanted, keep it but use the spec's reachable `99`/`100` boundary and annotate the deviation. As written, the plan silently overrides governing-spec guidance with no `DEVIATION` rationale.

**2. Two spec-enumerated cases are dropped without justification.**
The governing spec lists eight cases; the plan covers six. Missing:
  - *"should skip a lexicographically-earlier non-digit-prefixed file when the digit-prefixed file sorts last"* — `aa-notes.md` + `02-b.md` → 3. The spec calls this a deliberate **complement** to the `zz-notes` case the plan keeps (it exercises the opposite lexicographic placement of the stray non-digit file). Dropping it loses intended branch-symmetry coverage.
  - *"double-digit file as sole entry"* — `10-c.md` → 11, guarding an off-by-one specific to multi-character digit prefixes.
  Either add both, or state why they are redundant with kept cases. Note the plan *replaced* these spec-endorsed cases with a spec-discouraged one (issue 1) — a net swap away from the spec's own coverage intent.

### Positive Notes
- Every asserted value is arithmetically correct against the real function — no fantasy values, no off-by-one.
- Setup notes are concrete and grounded (`tmp_path`, real `.write_text("")` files, "no mocking — the function reads the real directory through `Path.glob`"), matching the spec's "fully-pure-over-real-filesystem" characterization.
- The gap case (`01/02/05`→6) correctly pins max+1 vs. a naive count+1 (`4`) — the exact silent-correctness distinction that motivates the task.
- Descriptive per-case names carry the intent; phasing is coherent.

### Minor
- **Test Command deviates from the established convention.** The infra task and every prior test plan (e.g. `26-...md`) prescribe `` `uv run pytest tests/ -v` ``; this plan uses `` `uv run pytest tests/test_main.py -v` ``. Since the change is additive to `test_main.py` it still runs, but the narrowed command drops the full-suite safety net the convention relies on. Align to `tests/ -v` unless there's a reason to scope down.

## Deferred observations
- Affects: whoever owns artifact numbering next — The lexicographic-sort latent bug the spec documents (a directory holding both `"99-x.md"` and `"100-y.md"` returns `100` and collides on the next write, because `:02d` pads to a *minimum* not a *fixed* width) is a real gap in `_next_number`'s numbering scheme, unreachable only while milestone counts stay ≤ 99. It lies outside this test-only milestone's boundary (fixing it means changing `_next_number`/its caller, not `tests/test_main.py`), so it is not a finding here — but it is the substance behind issue 1 and belongs on the radar of whoever next touches artifact numbering.
