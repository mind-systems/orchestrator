## Plan Review Summary

**Plan:** 29.1 — the outcome exceptions live in `errors.py`
**Task spec:** `.ai-factory/specs/trickster77777/0068-the-outcome-exceptions-live-in-errors.md` (governing: `.ai-factory/ARCHITECTURE.md` § Dependency Rules, § Folder Structure)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.** `errors.py` is in the Vocabulary layer (ARCHITECTURE.md § Dependency Rules) and imports nothing from the package. The new edges `main` → `errors`, `agents` → `errors` and `usage` → `errors` all point down. Removing `usage` → `agents` takes away an edge that was never allowed: `usage` → `agents` is not a named within-layer edge.
- **Rules — WARN.** `.ai-factory/RULES.md` does not exist. There is also no `.ai-factory/skill-context/aif-review/SKILL.md`.
- **Roadmap — OK.** The plan matches contract line 29.1 in `.ai-factory/roadmaps/trickster77777.md` and its task spec 0068.

### Ground-truth check (plan vs. code)

I checked each of the plan's claims against the current files:

- `orchestrator/agents.py` defines the six classes in the stated order, between `_classify_result` and `_sorted_nvm_node_dirs`. ✅
- `agents.py` raises exactly `NetworkError`, `RateLimitError`, `EscalationError` and `MissingArtifactError`. `HaltError` and `PipelineStopError` appear only in the class definitions and in the `EscalationError` docstring, and both move. So the four-name import is right. ✅
- The `main.py` line-13 import, the `usage.py` line-9 import, the `tests/test_agents.py` parenthesized block and the `tests/test_main.py` line-13 import all match the plan. ✅
- The plan has a DEVIATION-style note: there is a second `getattr(agents_module, "HaltError", None)` read, at `test_process_task_resume_past_max_iterations_raises_halt_error` (test_main.py, around line 1042). That is correct, and the spec missed it. `agents_module` has no other use in `tests/test_main.py`, so replacing the import is safe. ✅
- No other module (`resume.py`, `runtime.py`, `notify.py`, the empty `__init__.py`) imports these exceptions from `agents`. ✅

### Critical Issues

1. **The verification step cannot detect a stale `agents` import, which is the one failure the task spec warns about.** (Task "Confirm no stale references and a green suite")

   After this change, `agents.py` will hold `EscalationError`, `MissingArtifactError`, `NetworkError` and `RateLimitError` in its namespace, because it imports them from `errors`. So `from orchestrator.agents import RateLimitError` keeps working, and `uv run pytest` stays green even if a test import was missed. The spec names this under "What breaks on contact": a name reachable through `agents` "would keep every old import working and hide a missed one". The plan leaves the grep as the only guard, and that grep has two holes. I reproduced both with a scratch file and the plan's exact command on this machine:

   - **`[^\n]` does not mean "not a newline" in a POSIX/ERE bracket expression.** It means "neither a backslash nor the letter `n`". Any lowercase `n` between `agents` and the exception name stops the match. `from .agents import Implementer, HaltError` was **not** matched; `from .agents import HaltError` was.
   - **Multi-line imports are invisible to a line-oriented grep.** `tests/test_agents.py` imports through a parenthesized `from orchestrator.agents import (` block, one name per line. A leftover `    EscalationError,` inside it was **not** matched. This is the exact block the plan edits.

   **Fix:** replace the first grep with a check that reads the import statements themselves. For example:

   ```bash
   uv run python -c "
   import ast, pathlib, sys
   six = {'HaltError','RateLimitError','NetworkError','MissingArtifactError','PipelineStopError','EscalationError'}
   bad = []
   for p in [*pathlib.Path('orchestrator').glob('*.py'), *pathlib.Path('tests').glob('*.py')]:
       for n in ast.walk(ast.parse(p.read_text())):
           if isinstance(n, ast.ImportFrom) and (n.module or '').split('.')[-1] == 'agents':
               bad += [f'{p}:{n.lineno} {a.name}' for a in n.names if a.name in six]
           if isinstance(n, ast.Attribute) and n.attr in six and isinstance(n.value, ast.Name) and n.value.id in {'agents','agents_module'}:
               bad.append(f'{p}:{n.lineno} {n.value.id}.{n.attr}')
   print('\n'.join(bad)); sys.exit(1 if bad else 0)
   "
   ```

   It must print nothing and exit 0. If the implementer keeps a grep, it should use `.*` instead of `[^\n]*`, and add a separate check of the `from orchestrator.agents import (` block in `tests/test_agents.py`. One option is `sed -n '/from orchestrator.agents import (/,/)/p' tests/test_agents.py | grep -E 'HaltError|RateLimitError|NetworkError|MissingArtifactError|PipelineStopError|EscalationError'`, which must return nothing.

### Positive Notes

- The plan follows the code where the spec was incomplete: it found the second `getattr(agents_module, …)` read and explained the change at the top of the plan.
- The import list for `agents.py` is limited to the names actually raised, and the plan tells the implementer to grep before adding `HaltError` or `PipelineStopError`. This keeps the "no re-export" rule tight.
- The move is character-for-character and keeps the order, including the `EscalationError` docstring that says it is "NOT a HaltError subclass". `test_escalation_error_is_not_halt_error` keeps guarding the hierarchy.
- The task dependencies are ordered correctly, and the plan correctly says no new test is needed.
