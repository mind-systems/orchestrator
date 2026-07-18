> Owner: trickster77777@gmail.com

# Project Roadmap

> Orchestrator — AI-driven multi-agent pipeline that autonomously plans, implements, and reviews code tasks.

## Self-hosting hardening

The orchestrator generates every project's code — including its own — so a silent defect here multiplies across the whole fleet: a wrong result is x10 outside, x100 at scale. This direction hardens the tool's own correctness — per-project configuration and artifact numbering below.

### Phase 3 — Per-project configuration

`load_config()` (`config.py:23`) reads one global `orchestrator.json` (or the `ORCHESTRATOR_CONFIG` path) and applies it to every target project uniformly — `max_iterations`, usage thresholds, `enable_phase_sessions`, Telegram routing, and `roadmap_path` are all fleet-wide. There is no way for project A to run with different settings than project B without editing the global file back and forth. The behavior ТЗ is written doc-first in `docs/configuration.md` § Оверлей под проект (already done); this task implements to it.

- [x] **3.1 — Per-project config overlay — different projects, different settings** — add `load_config(project_dir: Path | None = None)`: load and validate the global base as today (the four required keys still required in the base), then if `project_dir/.ai-factory/orchestrator.json` exists, shallow-merge its keys over the base before building `OrchestratorConfig` — project keys win, absent keys inherit, the four required keys are NOT required in the override, `telegram_alerts` replaces (not unions), and the override's `roadmap_path` gets the same relative/no-`..` guard then flows through the existing three-state resolver unchanged. Malformed override JSON → `SystemExit` naming the override path. `cli()` (`main.py:490`) passes the run's resolved project dir so the overlay applies before roadmap resolution. Absence of the override file is byte-stable — identical to today (hard acceptance). Unit tests in `test_config.py` pin byte-stable absence, precedence, partial override, list-replace, the guard, and malformed JSON. Spec: `.ai-factory/specs/trickster77777/21-per-project-config-overlay.md`. [9m 43s]

### Phase 4 — Artifact numbering correctness

`_next_number` (`main.py:84`) finds the next artifact index by lexicographically sorting the dir's `*.md` and taking the last digit-prefixed stem + 1 — a lexicographic-vs-numeric sort trap. Numbers are `:02d` (minimum width, not fixed), so once a per-roadmap artifact dir crosses 100 files, `"100-y.md"` sorts before `"99-x.md"` and the function returns 100 while `100-y.md` already exists — a duplicate-number collision. Surfaced as a deferred observation on the `_next_number` tests milestone, where the fix lay outside that test-only boundary.

- [x] **4.1 — `_next_number`: pick by numeric max, not lexicographic last** — replace the `sorted(glob) → reversed → first digit-prefix + 1` logic (`main.py:89-92`) with a numeric max: over every `*.md`, parse the leading digit run of the stem (`stem.split('-',1)[0]` when `isdigit()`), return `max(...) + 1`; no digit-prefixed file → keep the `len(existing) + 1` fallback; empty dir → `1`. Kills the width-boundary collision (`99-x.md` + `100-y.md` → `101`, not the already-used `100`). The empty and all-non-digit contracts stay byte-identical — the only behavior change is at mixed digit widths (≥100). Update the `_next_number` characterization test that pinned the buggy mixed-width case (`['9-a.md','10-b.md']`) to assert the corrected max-based result, and add the explicit 99/100→101 boundary case. Touch `main.py` + `tests/test_main.py` only. Spec: `.ai-factory/specs/trickster77777/22-next-number-numeric-fix.md`. [12m 17s]

## Reserved-words language conformance

The skills family speaks one shared vocabulary (`skills/docs/reserved-words.md`) — a **naming-only contract**: reserved is the meaning, not the spelling; typography is never swept. This direction retires the synonym `milestone` for the reserved word `task` across the whole repository. Governing handoff: [`../handoffs/07-language-contract-softened-to-naming-only.md`](../handoffs/07-language-contract-softened-to-naming-only.md).

### Phase 5 — Code and test identifiers speak `task`

The Python surface names the processed unit `milestone` throughout — the `Milestone` dataclass (`roadmap.py`), `process_milestone` (`main.py`), the `milestone_*`/`milestones_*` locals, `state.milestones_done`, and the `_find_milestone_line`/`mark_done`/`mark_skipped` parameters — mirrored across the `tests/` suite. This phase renames every identifier to `task`, the canonical form the later phases reference. Behavior-neutral: the counter is in-memory and the on-disk sidecar keys (`planner`, `implementer`, `step`, `elapsed`) are untouched, so resume is byte-stable. Full coverage by the existing tests makes the rename mechanical and self-verifying.

- [x] **5.1 — Rename `milestone` code identifiers to `task`** — the processed roadmap unit is the reserved word `task`, but the Python surface still names it `milestone`: the `Milestone` dataclass, `process_milestone`, `_find_milestone_line`, `_detect_milestone_step`/`_detect_test_milestone_step`, the `milestone_index`/`milestone_start`/`milestone_title`/`milestone_description` locals, `state.milestones_done`, `milestones_after_breakpoint`, and the matching `tests/` names + `_MilestoneStub`. Rename every identifier (and the in-code docstrings/comments that say "milestone") to `task` across `orchestrator/*.py` and `tests/*.py`, symbol-aware — leave user-facing string literals, alert tokens, `print` wording, and config untouched (Phase 6), even where both sit on one line (`notify(…, "Milestone done: {task.title}", "milestone")`). Behavior-neutral, resume-safe (no on-disk format touched). Verify: `uv run pytest` green; residual `milestone` grep hits only inside Phase-6 string literals. Spec: `.ai-factory/specs/trickster77777/24-code-identifiers-milestone-to-task.md`. [32m 49s]

### Phase 6 — User-facing runtime surface speaks `task`

The operator meets the word "milestone" at run time: the Telegram alert tokens `milestone` / `milestone-fail` (matched in `notify.py`'s `_FAIL_ALERTS`, emitted at the `notify()` call sites, and listed under `telegram_alerts_example_all` in `orchestrator.json` and its example — the token vocabulary's default lives there, not in `config.py`, which only declares the field with an empty-list default), the "Milestone done" message text, and the `runtime.py` run-summary "{n} milestones done". This phase renames the alert tokens to `task` / `task-fail` and the prose to `task`. It is a **breaking change to the config token vocabulary** — an existing `orchestrator.json` listing `milestone-fail` must be updated by hand — accepted so the operator sees `task` coherently in Telegram and the console.

- [x] **6.1 — User-facing runtime surface speaks `task`** — rename the last surface where the operator still meets "milestone": Telegram tokens + text as one indivisible slice (silent-failure risk if split) — `notify.py`'s `_FAIL_ALERTS`, the `notify()` call-site tokens/text in `main.py` ("milestone"/"milestone-fail"→"task"/"task-fail", "Milestone done"→"Task done"), and `orchestrator.json` + `.example`'s `telegram_alerts` values only (never credentials). Plus non-breaking prose: the `MILESTONE`/`TEST MILESTONE` header, skip/exception messages, pending-count prints, CLI `--help` text, and `runtime.py`'s sigint print + run-summary. Assumes 5.1 landed — code references are already `task.title`/`state.tasks_done`; only strings/tokens change here. Matching test updates in `test_notify.py`, `test_main.py`, `test_runtime.py`, `test_config.py` (incl. the three alert-token test names). Verify: `uv run pytest` green; `grep -rn "milestone" orchestrator/*.py tests/*.py` → zero hits. Spec: `.ai-factory/specs/trickster77777/25-user-facing-runtime-milestone-to-task.md`. [8m 17s]

### Phase 7 — Prompt bodies speak the language

`planner.md`, `test-planner.md`, and `reviewer.md` still name the roadmap unit with the retired word `milestone`. This phase conforms it to the reserved word `task`, plus one synonym fix in passing ("full specification" → "full task spec"); the prompts' existing spellings of the other reserved terms are already conformant — typography is never swept; protocol literals (`## Deferred observations`, `- Affects:`, `PLAN_REVIEW_PASS`/`REVIEW_PASS`, `Spec:`/`Governing spec:` tags) stay legacy. The plan's own checklist "task" (`## Tasks`, `**Task N:**`) is untouched — it reads consistently at plan altitude exactly as `phase` already does at both roadmap and plan altitude, not a collision. Because the prompts shape every plan and review the orchestrator writes, this is the phase that makes the produced artifacts speak the language going forward. It depends on Phase 5 for a consistent reading only, not mechanically.

- [x] **7.1 — Prompt bodies speak the language** — `milestone`→`task` for the roadmap unit across `planner.md`, `test-planner.md`, `reviewer.md` prose, plus one synonym fix: "full specification"→"full task spec" (plain spelling; "named roadmap" and the deferred-observations prose already conform — typography is never swept). No plan-structure change — `## Tasks`/`**Task N:**` and every plan-checklist "task" stay exactly as-is (not a collision; `task` reads consistently at plan altitude like `phase` already does, per `using-the-language.md` § "The one rule"). Guard: `## Deferred observations`, `- Affects:`, `PLAN_REVIEW_PASS`/`REVIEW_PASS`, `Spec:`/`Governing spec:` tags are protocol literals, byte-for-byte (cross-repo contract, skills handoff 21). Verify: `grep -rniE "\bmilestone" orchestrator/prompts/*.md` → zero hits. No tests. Spec: `.ai-factory/specs/trickster77777/26-prompt-bodies-speak-the-language.md`. [5m 58s]

### Phase 8 — Docs and meta speak the language, skills renamed

The docs and project meta (`docs/*.md`, `CLAUDE.md`, `.ai-factory/ARCHITECTURE.md`) still speak the retired vocabulary. This phase conforms it — `milestone`→`task`, word choice only, protocol literals and tags left legacy, typography never swept — split in two: **8.1** the vocabulary pass, **8.2** the two rescue-skill renames (done doc-first; skills 16.1 reconciles).

- [x] **8.1 — Docs and meta speak the language** — conform `milestone`→`task` across the Russian-majority `docs/*.md`, `CLAUDE.md`, `.ai-factory/ARCHITECTURE.md` (incl. `## Features` labels — commit hashes stay). Inflect the loanword correctly: `milestone-ы`→`task-и` (велярное таски, not «таскы»), `-ов`/`-ами` unchanged; one synonym fix ("spec notes"→"task specs"), no typography sweep; reflect `process_task()` (post-5.1). Leave `/milestone-rescue*` (8.2), protocol literals, tags, `phase`; `README.md` verify-only. Spec: `.ai-factory/specs/trickster77777/27-docs-and-meta-speak-the-language.md`. [10m 36s]

- [x] **8.2 — Rename the rescue-skill references** — `/milestone-rescue`→`/task-rescue`, `/milestone-rescue-audit`→`/task-rescue-audit` in `docs/how-it-works.md:25` and `docs/non-convergence.md:37` only. Executed doc-first by owner decision (docs are governing specs and lead code): the docs carry the target names, skills' task 16.1 (spec `skills/.ai-factory/specs/71-rescue-skills-rename.md`) reconciles the skills repo to them. Frozen history keeps the old names. Spec: `.ai-factory/specs/trickster77777/28-rename-rescue-skill-references.md`.

## Prompt–execution alignment

The agent prompts are meant to describe what the pipeline actually does. Where a prompt drifts from execution reality it plants instructions and plan artifacts the pipeline never carries out — noise that the planner spends tokens authoring and a reader mistakes for real behavior. This direction realigns the prompts with what the orchestrator executes.

### Phase 9 — Drop the vestigial Commit Plan instruction

The planner is told to author a multi-commit `## Commit Plan` with checkpoints every 3–5 tasks (`planner.md:111–123`, plus Important Rule #7), and the implementer reads those checkpoints as commit guidance (`implementer.md:32`). Nothing executes it: `_git_commit` (`main.py:177`) makes exactly one commit per completed task — `git add -A` and a single `git commit` whose message is the task title alone — and the implementer is told not to commit at all. So the checkpoint plan never materializes, and it contradicts the atomic-task-equals-one-commit model: a genuinely separable commit would be a separate task, not an in-plan checkpoint. This phase removes the instruction so a plan carries only what the pipeline runs.

- [x] **9.1 — Drop the vestigial Commit Plan instruction** — `planner.md` tells the planner to emit a `## Commit Plan` with checkpoints every 3–5 tasks (lines 111–123) plus Important Rule #7, and `implementer.md:32` frames commits as "checkpoints"; but `_git_commit` (`main.py:177`) makes exactly one commit per completed task (message = the task title), so the multi-commit plan is never executed and contradicts the atomic-task-equals-one-commit model. Delete the Commit Plan heading + example + rules block and rule #7 from `planner.md` (renumber the remaining rules contiguously); reduce `implementer.md:32` to a one-liner that commits are the orchestrator's concern. Prompt-only — do not touch `_git_commit`, and do not conform `milestone → task` vocabulary here (Phase 7's scope). Spec: `.ai-factory/specs/trickster77777/23-remove-vestigial-commit-plan.md`. [4m 50s]

---STOP---

- [ ] **Interactive REPL mode** — Bare `uv run orchestrator` (no subcommand) currently defaults to implement on current dir. Replace with an interactive session: load config from `~/.orchestrator.json`, display settings on entry, prompt `>` with readline history. Commands: `implement <path>`, `test <path>`, `set <key> <value>` (type-validated, in-session only), `show`, `save` (atomic write to config file via tmp+replace), `help`, `exit`. Ctrl+C during pipeline → stop run, return to prompt. New `orchestrator/repl.py`; `cli()` routes `args.command is None` to `run_repl(config, config_path)`; `load_config()` return type changes to `tuple[OrchestratorConfig, Path]`. Zero new dependencies — `readline` (stdlib). Update `CLAUDE.md` Commands section; mention REPL in `docs/workflow.md`. Spec: `.ai-factory/specs/trickster77777/01-repl.md`.

---STOP---

## Codex backend adaptation

The orchestrator currently treats Claude Code as the only executable agent runtime: `agents.py` shells out to `claude`, parses Claude `stream-json`, resumes Claude sessions, maps Claude tool names, and `usage.py` gates on `claude /usage`. This direction turns that runtime dependency into an explicit backend boundary so the existing file-protocol pipeline can run on Codex without weakening the proven Claude path. The pinned contract is parity first: plan, plan-review, implement, review, sidecar resume, PASS signals, and commit behavior stay unchanged unless a later task explicitly changes them.

### Phase 10 — Agent backend boundary

The first blocker is structural: `_run_claude()` is both process runner, output parser, retry policy, session carrier, tool mapper, and error classifier. Codex support needs a narrow backend interface before any Codex command is introduced, otherwise the second runtime will fork the whole `PlannerReviewer` / `PlanReviewer` / `Implementer` surface. This phase extracts the runner contract around the existing Claude behavior while preserving current defaults and tests.

### Phase 11 — Codex process runner and output contract

Once the backend boundary exists, Codex needs its own process runner with a stable output contract: command construction, cwd handling, prompt/system-prompt delivery, result extraction, nonzero-exit handling, interrupt cleanup, and enough run identity to populate the existing sidecar fields. The risk is not launching Codex; the risk is pretending Claude `session_id` and Codex continuation semantics are identical. This phase proves the Codex runner can return the same orchestrator-level shape without changing the file protocol.

### Phase 12 — Session and resume semantics

The orchestrator's convergence model depends on persistent planner/reviewer and implementer context: sidecar JSON stores the planner and implementer session IDs, phase sessions optionally carry across tasks, and resume starts from a detected step rather than replaying finished work. Codex may expose continuation through a different session/thread/task identifier, or may require a different prompt handoff strategy. This phase defines the backend-neutral resume contract and pins which guarantees are required for mid-task recovery, phase carryover, and re-review context.

### Phase 13 — Tools, permissions, and sandbox mapping

The existing agents pass Claude tool names (`Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`) and rely on `--dangerously-skip-permissions` plus local Claude settings for planner writes under `.ai-factory/plans/`. Codex has a different permission and tool surface, so the backend must translate intent rather than copy strings. This phase maps the orchestrator's required capabilities to Codex permissions, keeps write scope explicit, and documents what cannot be enforced through the same mechanism.

### Phase 14 — Usage gating and operational halts

`usage.py` currently shells out to `claude /usage` and parses Claude-specific "Current session" and "Current week" percentages before each task. Codex may not expose an equivalent CLI usage command or the same quota windows. This phase makes usage gating backend-aware: Claude keeps its current guard, Codex either gets a real parser for its available signal or an explicit disabled/unknown state that degrades to a warning without masquerading as protection.

### Phase 15 — Configuration, docs, and runtime selection

After both backends exist, the operator needs a clear way to choose one per run or per project without editing code. This phase adds configuration for `agent_backend`, backend-specific model/effort defaults, and documentation that separates Claude activation (`~/.claude`) from Codex activation (`AGENTS.md`, skills, permissions). The goal is a boring switch: existing Claude users see byte-stable behavior by default, while Codex runs are intentionally opted in and visibly reported in logs.

### Phase 16 — Parity validation on a disposable target

Codex support is not done when the unit tests pass; the orchestrator's real contract is a full task loop through files. This phase runs the Codex backend against a disposable target project with a tiny roadmap task, verifies plan creation, plan-review PASS, implementation, review PASS, sidecar resume files, git commit behavior, interrupt handling, and failure reporting. Any divergence becomes either a documented backend difference or a blocking fix before Codex is allowed on real project roadmaps.
