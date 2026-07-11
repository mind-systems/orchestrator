# Code Review: Per-roadmap artifact subdirectories

Reviewed `git diff HEAD` in full — `orchestrator/main.py`, `tests/test_main.py`, `docs/how-it-works.md`, `CLAUDE.md`. Read the surrounding code in `main.py` (`process_milestone`, `_run_dynamic_loop`, both loop setups) and `resume.py` (`_detect_step`, `_validate_sidecar_step`).

## Verification performed

- **`uv run pytest`**: 116 passed. The full pre-existing suite stays green, confirming the byte-stable-default guard (default pair → `None` → no subdir branch taken).
- Grepped every artifact-dir construction (`plans`/`reviews`/`plan-reviews`/`test-runs`) across `orchestrator/` — the only two `plans_dir` homes (`process_milestone` main.py:198, `_run_dynamic_loop` main.py:362) both apply `artifact_subdir`, and they derive it from the same value threaded through `_replace`/the loop param, so the number axis used by `_next_number` and the dir the plan is written to never diverge.

## Analysis

1. **Subdir key mapping** — `_artifact_subdir` (main.py:166) maps the exact default pair to `None` and everything else to `Path(relpath).stem`. Correct for `roadmaps/kg-wmservice.md` → `kg-wmservice`, `...-tests.md` → `...-tests`, `ROADMAP.watch.md` → `ROADMAP.watch` (`.stem` strips only the final suffix). Pinned by five unit tests.
2. **Threading** — `Mode.artifact_subdir` added last with a default, so the positional `IMPLEMENT_MODE`/`TEST_MODE` literals remain valid; both `_replace` sites set it, and `_run_dynamic_loop` receives the same value. `_detect_step`/`resume.py` unchanged — they consume the subdir'd dirs through existing parameters (glob is per-directory, so numbering correctly restarts at `01` in a fresh subdir per spec §Change.3).
3. **Test-mode siblings** — `_tests_sibling` yields `roadmaps/kg-wmservice-tests.md`, whose stem `kg-wmservice-tests` is a distinct subdir from the implement side's `kg-wmservice`; no filename contact, matching spec §Change.3.
4. **No path-traversal risk** — the subdir is a bare `.stem`, and task-12's `_resolve_roadmap_relpath` already rejects absolute/`..` roadmap paths upstream.
5. **Docs** — `how-it-works.md` (Russian, matching the file) and `CLAUDE.md` describe the flat-default / per-roadmap-subdir behavior; skills-repo mirrors correctly left out of scope per spec §Guards.

No correctness, security, or runtime concerns found. Implementation conforms to the plan and spec `.ai-factory/specs/13-artifact-subdirs.md`.

REVIEW_PASS
