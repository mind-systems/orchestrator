## Plan Review Summary

**Plan:** 29.3 — the port and the kind type live in `ports.py`
**Files targeted:** 5 (`orchestrator/ports.py` new, `orchestrator/agents.py`, `orchestrator/main.py`, `orchestrator/resume.py`, `tests/test_main.py`)
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap** — OK. The plan matches the contract line for 29.3 in `.ai-factory/roadmaps/trickster77777.md` (29.1 and 29.2 are `[x]`; 29.3 is the seam) and its task spec `.ai-factory/specs/trickster77777/0070-the-port-and-the-kind-type-live-in-ports.md`.
- **Architecture** — OK. `ARCHITECTURE.md` § Dependency Rules puts `ports.py` in Vocabulary and `resume.py` in The flow. The planned `ports.py` imports only stdlib, with no `TYPE_CHECKING` reach. `make_verifier` is retyped as `Callable[[VerifierProtocol, Path], VerifierProtocol]`, which removes the annotation edge to the role `PlannerReviewer`. After the change, `resume` imports only `ports` and `protocol`, both below its layer, so the `resume` → `agents` edge is gone. `agents` → `ports` and `main` → `ports` both point downward. § Folder Structure already lists `ports.py # Vocabulary: VerifierProtocol and the VerifyKind type`, and § Components already says the port and the kind type live in `ports.py`. No doc update is needed.
- **Rules** — WARN (informational): there is no `.ai-factory/RULES.md` and no `.ai-factory/skill-context/aif-review/SKILL.md`. No convention gate applies.

### Verification against the codebase

- `agents.py` defines `VerifierProtocol` and `VerifyKind` directly above `_review_verifier`, as the plan says. `make_verifier` is currently annotated `Callable[[PlannerReviewer, Path], VerifierProtocol]`.
- After the move, `agents.py` uses `Callable`, `NamedTuple` and `Protocol` only inside the moved classes, so the plan correctly drops the whole `from typing import …` line. `rg '\b(Callable|NamedTuple|Protocol)\b' orchestrator/agents.py` matches only the import line and the two class definitions.
- `main.py` imports `VerifyKind` from `.agents` and uses it only in `Mode.verify`. It never names `VerifierProtocol`: `process_task` calls `mode.verify.make_verifier(...)` without an annotation. The plan imports only `VerifyKind` and records this reading as an Assumption. That fits ARCHITECTURE's "edges are stated as directions, never as inventories of symbols", so it conforms to the spec and does not deviate from it. Placing the import after `.notify` and before `.protocol` matches the existing alphabetical order. `main.py` still needs its own `typing.NamedTuple` import for `Mode`, and the plan leaves it alone.
- `resume.py` uses `REVIEW_VERIFY` and `TEST_RUN_VERIFY` only inside the two wrappers at the end of the file. Deleting the wrappers and changing the import to `from .ports import VerifyKind` leaves no dangling reference.
- `tests/test_main.py` imports `_detect_task_step` and `_detect_test_task_step` from `orchestrator.resume`. No test patches `orchestrator.resume._detect_step`, `REVIEW_VERIFY`, `TEST_RUN_VERIFY`, the factories or `VerifyKind`, so local helpers that call the imported `_detect_step` behave identically. The helpers are `_`-prefixed and pytest will not collect them, so the test count stays the same. The current baseline is 226 passed.
- The helpers keep the original names, signatures and argument order. The positional `reviews_dir` and `test_runs_dir` arguments go to `_detect_step`, as before.
- `docs/`, `CLAUDE.md` and `ARCHITECTURE.md` do not mention the wrappers, so no doc is left stale.

### Critical Issues

None.

### Positive Notes

- The plan reasons about the one spec ambiguity (which names `main` imports) explicitly and avoids adding an unused import.
- It keeps the change behaviour-neutral: factory bodies, instance values and `_detect_step` stay byte-identical, and it explicitly refuses to touch Phase 26's `endswith` checks.
- Its closing grep checks target exactly the edges the spec says must disappear.

PLAN_REVIEW_PASS
