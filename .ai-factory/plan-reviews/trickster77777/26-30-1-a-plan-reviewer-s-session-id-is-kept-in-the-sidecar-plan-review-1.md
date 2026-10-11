## Plan Review Summary

**Plan:** 30.1 — a plan reviewer's session id is kept in the sidecar
**Files the plan targets:** 3 (`orchestrator/agents.py`, `orchestrator/main.py`, `tests/test_agents.py`)
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap:** OK. The plan matches the contract line `30.1` in `.ai-factory/roadmaps/trickster77777.md` (Phase 30, the open task above `---STOP---`). Its task spec `.ai-factory/specs/trickster77777/0066-a-plan-reviewers-session-id-is-kept.md` was read in full, and the plan covers each of its "What must be true after" points: the `attempt: int` parameter after `review_path`, the write right after `_run_claude` and before the review-file check, the caller passing `attempt`, and the three tests.
- **Governing spec:** OK. `docs/features/resume.md` § What the sidecar holds already describes the `plan-reviewer-<N>` key: N is the attempt in the artifact name, the key is written as soon as the reviewer returns (even with no review), and resume never uses it. The plan's "Docs: no" is correct.
- **Architecture:** OK. `.ai-factory/ARCHITECTURE.md` puts the sidecar helpers in a future `protocol.py`. That module does not exist yet, and Phase 29 creates it, after this task in file order. Using `_write_session` from `agents.py` is right for the current tree.
- **Rules:** `.ai-factory/RULES.md` is absent (WARN, non-blocking). `.ai-factory/skill-context/aif-review/SKILL.md` is absent.

### Verification against the codebase

- `PlanReviewer.review_plan(self, plan_path, review_path) -> bool` in `orchestrator/agents.py` matches the plan's description: it runs `_, sid = _run_claude(...)` and drops `sid`, then raises `MissingArtifactError` when the review file is absent. It writes `escalation` and `step` only on escalation and returns `_has_signal(review_text, "PLAN_REVIEW_PASS")`. Putting `_write_session` between the `_run_claude` return and the `if not review_path.exists():` check covers both the missing-artifact path and the escalation path, as the spec requires.
- `_write_session` reads the existing JSON, sets the key and replaces the file atomically. A re-run attempt therefore overwrites its own key, and keys from other attempts are kept, as the plan claims.
- The `sid` handling matches the existing `planner` and `implementer` writes. They also pass `_run_claude`'s returned id to `_write_session` unchanged, so no new edge case appears.
- `process_task` in `orchestrator/main.py` calls `plan_reviewer.review_plan(plan_path, plan_review_path)` inside `for attempt in range(counter, max_iterations + 1):`, and `plan_review_path` is built from the same `attempt`. So the key and the artifact number match. A grep over `orchestrator/` and `tests/` finds no other caller and no fake `review_plan` (in `tests/test_main.py`, `PlanReviewer` is only patched as fail-if-constructed). The three-argument signature breaks nothing else.
- Resume reads only `step`, `elapsed`, `escalation`, `planner` and `implementer`, through `.get` in `main.py` and `_detect_step` / `_validate_sidecar_step` in `resume.py`. Nothing checks the set of keys or whether the sidecar exists, so the new key does not change resume behaviour.
- Tests: both stubs return `"sid-1"`: `_stub_run_claude_writing` and the inline lambda in the missing-file test. So the exact-dict assertion `{"plan-reviewer-1": "sid-1"}` is correct for both tests. On the non-escalation and missing-file paths the stubs write nothing else to the sidecar, so equality is the right strength. `json` is already imported in `tests/test_agents.py`. The two docstrings that today say "no sidecar is written" are updated, as they should be.
- Baseline: `uv run pytest` passes (226 passed) before the change.

### Critical Issues

None.

### Positive Notes

- The write happens before the artifact check, so a session that produced no artifact still leaves its id. That is the case where a rescue most needs to ask the agent what happened.
- The plan keeps the escalation path's `step`/`escalation` writes and the return value unchanged, so the change only adds the new key.
- The plan states the "no plan-layer citations" rule for the docstring, which follows the global comment discipline.
- The tests pin the key name and the attempt number exactly. The spec notes these would fail silently at run time if wrong, so pinning them is justified under the silent-failure rule.

## Deferred observations

- Affects: skills — `orchestrator-artifacts` engine (sidecar fields) — The sidecar gains a `plan-reviewer-<N>` key family. The skills' `orchestrator-artifacts` mirror of the sidecar fields should list it so consumer skills (and any rescue procedure) know where to find a plan reviewer's session. The task spec's "What breaks on contact" section assigns this to the skills side, outside this task's file boundary. [routed → skills/.ai-factory/specs/trickster77777/0246-the-engine-names-the-plan-reviewer-session-keys.md]

PLAN_REVIEW_PASS
