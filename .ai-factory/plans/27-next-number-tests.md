# Test Plan: `_next_number` tests

## Context
`_next_number(directory)` (`orchestrator/main.py:84-93`) globs `*.md` in an artifact directory, sorts the results lexicographically, and returns `int(prefix)+1` for the highest digit-prefixed stem (falling back to `len(existing)+1` when no file has a digit prefix). Its result seeds every artifact filename for a milestone, so a wrong pick silently mints a duplicate `NN` or collides on merge — a silent correctness bug, never a crash. It currently has no test.

## Settings
- Testing: yes
- Logging: minimal
- Docs: no

## Test Command
`uv run pytest tests/ -v`

## Target Spec File
`tests/test_main.py`

## Tasks

### Phase 1: `_next_number` — empty, single, and gapped directories

- [x] **Task 1: `_next_number` — max-based numbering over well-formed files**
  Files: `tests/test_main.py`
  Setup notes: import `_next_number` from `orchestrator.main`; use pytest's `tmp_path` as the directory and create real files via `(tmp_path / "NN-slug.md").write_text("")`. No mocking — the function reads the real directory through `Path.glob`.
  Test cases:
  - `should return 1 when the directory is empty` (no files created — exercises the `if not existing: return 1` branch)
  - `should return one past the number when a single well-formed file exists` (create `03-x.md` → returns `4`)
  - `should return one past the highest number, not the count, when files exist with a gap` (create `01-a.md`, `02-b.md`, `05-c.md` → returns `6`, pinning max+1 vs. a naive count+1 that would return `4`)

### Phase 2: `_next_number` — mixed digit / non-digit stems

- [x] **Task 2: `_next_number` — reversed scan skips non-digit stems (both lexicographic placements)**
  Files: `tests/test_main.py`
  Test cases:
  - `should skip a lexicographically-later non-digit stem and fall through to the digit stem when it sorts first` (create `01-a.md`, `zz-notes.md`; sorted is `["01-a.md","zz-notes.md"]`, reversed visits `zz` first and skips it, then matches `01` → returns `2`)
  - `should skip a lexicographically-earlier non-digit stem when the digit stem sorts last` (create `aa-notes.md`, `02-b.md`; sorted is `["02-b.md","aa-notes.md"]`, reversed visits `aa` first and skips it, then matches `02` → returns `3`). Deliberate complement to the `zz-notes` case above — exercises the opposite lexicographic placement of the stray non-digit file, confirming the loop does not stop at the first non-digit stem regardless of where it sorts.
  - `should fall back to count + 1 when no file has a digit-prefixed stem` (create `notes.md`, `readme.md` → returns `3` via the `len(existing)+1` fallback line; the loop exhausts without returning)

### Phase 3: `_next_number` — double-digit rollover and the lexicographic-sort boundary

- [x] **Task 3: `_next_number` — zero-padded rollover, double-digit sole entry, and the mixed-width ordering invariant**
  Files: `tests/test_main.py`
  Test cases:
  - `should roll from single- to double-digit numbering within a zero-padded two-digit width` (create `08-a.md`, `09-b.md` → returns `10`; asserts the padded convention under which lexicographic and numeric order agree, so max-detection holds — the risk is in the sort, not the `int()` parse)
  - `should return the correct next number when the sole entry is already a double-digit file` (create `10-c.md` → returns `11`; guards an off-by-one specific to multi-character digit prefixes)
  - `should return 10 for a mixed-width set where '10' sorts before '9' as strings` (create `9-a.md`, `10-b.md`; string sort gives `["10-b.md","9-a.md"]`, reversed visits `9-a.md` first and returns `10` — a collision with the existing `10-b.md`). This is a **characterization** test: it pins the currently-produced value so a future change that drops zero-padding trips this test rather than silently colliding. Name the test so its intent is unmistakable and add a comment marking the asserted `10` as characterizing broken (non-padded) behavior, not correct behavior.

    **DEVIATION from `.ai-factory/specs/19-next-number.md` (Gotchas):** the spec recommends recording this latent boundary as a note "rather than a test asserting the ... broken behavior as correct." The roadmap contract line for this milestone (`ROADMAP_TESTS.md`, `## main.py`) instead explicitly directs this exact case — *"add a case documenting that a mixed-width `['9-a.md','10-b.md']` set sorts `10` before `9` as strings ... so a future change that drops padding trips a test."* The contract line is the governing instruction and supersedes the spec's softer guidance, so the characterization test is kept using the contract's exact filenames (`9-a.md`/`10-b.md`). For the reader: the *reachable* form of this same bug (per the spec) is `99-x.md`/`100-y.md`, live once milestone counts cross 99, since the caller's `:02d` pads to a minimum — not a fixed — width; fixing it means changing `_next_number`/its caller and is out of scope for this test-only milestone. See the Deferred observations of the plan review.
