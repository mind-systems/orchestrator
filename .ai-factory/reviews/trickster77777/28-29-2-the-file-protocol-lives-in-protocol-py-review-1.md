## Code Review Summary

**Files Reviewed:** 5 (`orchestrator/protocol.py` (new), `orchestrator/agents.py`, `orchestrator/main.py`, `orchestrator/resume.py`, `tests/test_agents.py`)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.** `.ai-factory/ARCHITECTURE.md` § Folder Structure names `protocol.py` as "Vocabulary: the file protocol — sidecar read/write, completion-signal and escalation recognition". § Dependency Rules requires the vocabulary layer to import nothing from the package at runtime. `protocol.py` imports only `json`, `os` and `pathlib.Path`. The new edges `agents` → `protocol`, `main` → `protocol` and `resume` → `protocol` all point downward, and no cycle is introduced.
- **Rules — WARN (non-blocking).** `.ai-factory/RULES.md` and `.ai-factory/skill-context/aif-review/SKILL.md` are absent.
- **Roadmap — OK.** The change implements open task 29.2 in `.ai-factory/roadmaps/trickster77777.md`, which sits directly below the `[x]` 29.1 seam. It matches the task spec `.ai-factory/specs/trickster77777/0069-the-file-protocol-lives-in-protocol.md` on every point:
  - all five helpers are moved with bodies and docstrings unchanged;
  - `protocol.py` has no package import;
  - `agents`, `main`, `resume` and `tests/test_agents.py` import from `protocol`;
  - `agents` re-exports nothing (it imports only the four names its roles use, and not `_read_sessions`);
  - no new test is added.

### Verification

- **Bodies unchanged.** The bodies in `protocol.py` match the deleted `agents.py` definitions line for line: the five-line window in `_has_signal`, the `## Escalation` scan, and the `'.json'`/`'.json.tmp'` atomic write through `os.replace`. The sidecar format and the recognition rule are therefore unchanged.
- **`agents.py` still resolves every name.**
  - The four names it imports from `protocol` cover every use in `PlannerReviewer.plan`/`.review`, `PlanReviewer.review_plan` and `Implementer.implement`.
  - `json` is still used by stream-json parsing in `_run_claude`, `os` by `kill_active_child` and the env, and `Path` by `PROMPTS_DIR`. No import became dead.
  - Removing the block left two blank lines before `_is_overloaded`, which is the correct spacing.
- **`main.py` / `resume.py`.** Only the protocol names left the `.agents` import lines. The other names (`REVIEW_VERIFY`, `TEST_RUN_VERIFY`, the roles, `VerifyKind`) stay as they were, and the remaining `resume` → `agents` edge is 29.3's to remove. The new import in `main.py` keeps the block's alphabetical order.
- **Tests.** No test patches or `getattr`s the moved names on `agents`. The patch targets `agents._run_claude` and `agents.os.killpg` stay valid because neither moves. `uv run pytest`: 226 passed.
- **Docs.** No doc in `docs/` or `CLAUDE.md` names `agents.py` as the home of these helpers, so no doc edit is owed.

### Critical Issues

None.

### Positive Notes

- The move is mechanical and minimal. The `agents` import lists exactly what the roles use, so "re-exports nothing" holds structurally, not by convention.
- The `protocol.py` module docstring states its single concern with the wording of ARCHITECTURE's Folder Structure line.

REVIEW_PASS
