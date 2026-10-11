## Plan Review Summary

**Plan:** `.ai-factory/plans/trickster77777/28-29-2-the-file-protocol-lives-in-protocol-py.md`
**Task:** 29.2 — the file protocol lives in `protocol.py` (`.ai-factory/roadmaps/trickster77777.md`)
**Spec:** `.ai-factory/specs/trickster77777/0069-the-file-protocol-lives-in-protocol.md`
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.** `.ai-factory/ARCHITECTURE.md` § Folder Structure already lists `protocol.py` as "Vocabulary: the file protocol — sidecar read/write, completion-signal and escalation recognition". § Dependency Rules puts it in the Vocabulary layer, which must import nothing from the package at runtime. The plan's `protocol.py` imports only `json`, `os` and `pathlib.Path`, and its Verify step checks that it has no `from .` / `from orchestrator` import. The new edges (`agents` → `protocol`, `main` → `protocol`, `resume` → `protocol`) all point downward.
- **Rules — WARN (non-blocking).** `.ai-factory/RULES.md` is absent. `.ai-factory/skill-context/` is absent as well.
- **Roadmap — OK.** The task is the open 29.2 line in `.ai-factory/roadmaps/trickster77777.md`, directly below the `[x]` 29.1 seam. The plan matches the contract line: five helpers moved with unchanged bodies, no package imports, all four consumers import from `protocol`, `agents` re-exports nothing, behaviour stays the same, and no new test is added. The spec's governing chain (ARCHITECTURE § Dependency Rules / § Folder Structure, divergence note 0067) agrees with this.

### Verification against the codebase

- **The five helpers in `orchestrator/agents.py`.** They sit together between `RETRY_DELAY = 30` and `_is_overloaded`, in the order the plan gives: `_has_signal`, `_has_escalation`, `_escalation_excerpt`, `_read_sessions`, `_write_session`. Their bodies need only `json`, `os` and `Path`, so the import set the plan gives `protocol.py` is complete.
- **Imports that stay in `agents.py`.** `json` is still used by the stream-json parsing in `_run_claude`. `os` is still used by `kill_active_child`'s `os.killpg` and by the `_run_claude` env. `Path` is still used by `PROMPTS_DIR`. Keeping all three is correct.
- **Names `agents.py` needs from `protocol`.** The roles use `_write_session`, `_has_escalation`, `_escalation_excerpt` and `_has_signal` (`PlannerReviewer.plan`/`.review`, `PlanReviewer.review_plan`, `Implementer.implement`). `_read_sessions` has no use in `agents.py` beyond its definition. The four-name import is therefore exact.
- **Other consumers.** `main.py` imports `_read_sessions, _write_session` from `.agents`. `resume.py` imports `_read_sessions` from `.agents`. Both edits in the plan are correct and leave the other names on those lines alone. In `main.py`, `.protocol` goes between `.notify` and `.resume` to keep the alphabetical order. No other module in `orchestrator/` refers to these names.
- **Tests.** `tests/test_agents.py` imports all five names from `orchestrator.agents`. No test patches them or `getattr`s them on `agents`, `main_module` or `resume`. The two mentions in `tests/test_main.py` are comments only. The `monkeypatch.setattr(agents.os, "killpg", …)` patch targets `kill_active_child`, which stays in `agents`, so it is unaffected. The role tests patch `agents._run_claude`, which does not move here, so they stay valid, as the spec notes.
- **Docs.** `CLAUDE.md` names `agents.py` only for the roles and `_run_claude()`, and no doc names where these helpers live. "Docs: no" is therefore right for this task. The stale skills-side mirror reference (`skills/src/skills/orchestrator-artifacts/SKILL.md` § "Mirrors-the-orchestrator invariant") is already given to 29.7's hand-off message. It is not part of this task.

### Critical Issues

None.

### Positive Notes

- The plan states its ground truth and checks it: which names `agents` still needs, which stdlib imports survive the move, and that nothing patches the moved names.
- It leaves out `_read_sessions` from the `agents` import instead of importing it out of habit, and it bans re-exports explicitly. Together these hold the "re-exports nothing" contract.
- The Verify step checks the structure (definitions only in `protocol.py`, no package import there), not just a green suite.
- It keeps the remaining `resume` → `agents` edge for 29.3 and does not widen this task's scope.

PLAN_REVIEW_PASS
