# Next Artifact Number Derivation — Test Plan

**Date:** 2026-07-13
**Source:** roadmap-test-coverage agent

## Source Overview

`_next_number(directory)` (`orchestrator/main.py:84-93`) computes the next sequential artifact number for a milestone's plan/review/test-run files: it globs `*.md` in a directory, sorts lexicographically, and walks from the end looking for the first filename whose stem's prefix-before-first-hyphen is all-digits, returning that number + 1 (falling back to `len(existing) + 1` if no file has a digit prefix). It is called once per milestone iteration at `_run_dynamic_loop` (`main.py:403`) against `plans_dir` — the per-roadmap artifact subdirectory (`ai_factory/plans[/artifact_subdir]`) set up via `_artifact_subdir(relpath)` — and its result seeds `seq = f"{milestone_index:02d}"` used to name every artifact for that milestone across `plans/`, `plan-reviews/`, and `reviews/`/`test-runs/`. The roadmap itself (task 13, "Per-roadmap artifact subdirectories") calls this out explicitly: before subdirs existed, concurrent runs or merged foreign plans could make `_next_number` mint a duplicate `NN`, producing a real file collision or silent gap on merge — not a crash. A wrong answer here is a silent correctness bug (wrong or colliding filename), never an exception.

## Instantiation

- Call `_next_number(directory)` directly (from `orchestrator.main`); it is a pure function of the filesystem — no fixture, no constructor, no mocking needed.
- Use pytest's `tmp_path` fixture as `directory`, creating real files via `(tmp_path / "01-slug.md").write_text("")` or `.touch()`. `Path.glob("*.md")` reads the real directory, so setup must create actual files (empty content is fine — only the filename is inspected).
- No monkeypatching surface exists (no I/O other than the glob itself, no globals, no caching).

## Existing Coverage

None. `grep -n "_next_number" tests/test_main.py` returns no matches. The function is only exercised indirectly (and untested) through `_run_dynamic_loop` / `process_milestone` integration paths.

## Test Cases

### Empty / single / multiple well-formed files

- **should return 1 when the directory is empty**
  Exercises: `_next_number`
  Setup: pass an empty `tmp_path` directory (no files created). Asserts the `if not existing: return 1` branch.
- **should return one past the number when a single well-formed file exists**
  Exercises: `_next_number`
  Setup: create `tmp_path / "03-some-slug.md"`. Assert return value is `4`.
- **should return one past the highest number, not the count, when multiple well-formed files exist with a gap**
  Exercises: `_next_number`
  Setup: create `01-a.md`, `02-b.md`, `05-c.md` (3 files, highest number 5). Assert return value is `6` — this pins that the function is max-based, not count-based; a naive `len(existing) + 1` would wrongly return `4`.

### Mixed digit and non-digit stems (reversed-lexicographic scan)

- **should skip a lexicographically-later non-digit-prefixed file and fall through to the last digit-prefixed one**
  Exercises: `_next_number`
  Setup: create `01-a.md` and `zz-notes.md`. `sorted()` gives `["01-a.md", "zz-notes.md"]`; `reversed()` visits `"zz-notes.md"` first (stem `"zz"`, not digit — skipped), then `"01-a.md"` (stem `"01"`, digit — matches). Assert return value is `2`, confirming the loop does not stop at the first non-digit stem it meets and does not incorrectly fall back to the `len(existing)+1` branch just because the lexicographically-last file is non-numeric.
- **should skip a lexicographically-earlier non-digit-prefixed file when the digit-prefixed file sorts last**
  Exercises: `_next_number`
  Setup: create `aa-notes.md` and `02-b.md`. `sorted()` gives `["02-b.md", "aa-notes.md"]`; reversed visits `"aa-notes.md"` first (skip), then `"02-b.md"` (match). Assert return value is `3` — complements the previous case by exercising the opposite lexicographic placement of the stray non-digit file.
- **should fall back to count + 1 when every file lacks a digit-prefixed stem**
  Exercises: `_next_number`
  Setup: create only `notes.md` and `readme.md` (2 files, neither digit-prefixed). Assert return value is `3` (`len(existing) + 1`), exercising the final fallback line — the loop exhausts without ever returning.

### Double-digit rollover and lexicographic sort ordering

- **should correctly roll from single- to double-digit numbering within the same zero-padded width**
  Exercises: `_next_number`
  Setup: create `08-a.md` and `09-b.md` (both zero-padded to 2 digits, so string and numeric order agree). Assert return value is `10`, confirming `int()` parsing itself has no zero-padding/rollover issue — the risk is purely in the sort, not the parse.
- **should return the correct next number when reading a directory that already contains a double-digit file as the sole entry**
  Exercises: `_next_number`
  Setup: create only `10-c.md`. Assert return value is `11` (guards against any off-by-one specific to multi-character digit prefixes).

## Gotchas

- **Lexicographic sort, not numeric sort — real latent gap once digit-width crosses a boundary.** `sorted(directory.glob("*.md"))` sorts by string form. Verified empirically: `sorted(["99-x.md", "100-y.md"]) == ["100-y.md", "99-x.md"]` — a 3-digit number sorts *before* a 2-digit one. Since the reversed scan starts from the lexicographic maximum, a directory containing both `"99-x.md"` and `"100-y.md"` would visit `"99-x.md"` first (it's lexicographically last) and return `100`, silently ignoring the fact that `100-y.md` already exists and colliding with it on the very next write. This is the same class of bug documented for `_resolve_claude`'s nvm-version sort (`.ai-factory/specs/19-resolve-claude-cli.md`).
- **Whether this is reachable in practice depends on an invariant `_next_number` itself does not enforce.** The only call site (`_run_dynamic_loop`, `main.py:403`) feeds its result straight into `process_milestone`, which formats it as `seq = f"{milestone_index:02d}"` (`main.py:211`) — zero-padded to a *minimum* of 2 digits, not a *fixed* width. For milestone counts 1-99 this keeps every stem the same width (2 digits) so lexicographic and numeric order agree and the bug above cannot trigger. But `:02d` does not clamp — the 100th milestone in one directory produces `"100-slug.md"` (3 digits) sitting alongside `"99-slug.md"` (2 digits), and the sort-ordering bug becomes live on milestone 101. This is a real latent gap in the numbering scheme, not just a hypothetical: nothing pads to a fixed width, and nothing in `_next_number` or its caller checks for the boundary. Worth a note for whoever owns artifact numbering next, rather than a test asserting the (currently unreachable at low milestone counts) broken behavior as correct.
- **No test needed for a directory containing non-`.md` files** (e.g. a stray `.json` sidecar) — `directory.glob("*.md")` already filters those out at the OS level before any logic in `_next_number` runs; this is not a silent-failure surface, it's the glob doing its documented job.
- **No mocking needed anywhere.** This is the rare fully-pure-over-real-filesystem case: `tmp_path` + real file creation exercises the exact code path with no monkeypatching, unlike most of this codebase's other silent-failure surfaces.
