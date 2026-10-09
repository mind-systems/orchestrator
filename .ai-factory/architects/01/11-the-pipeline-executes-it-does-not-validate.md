# Snapshot 11 — the pipeline executes, it does not validate

Head 01, orchestrator. Written 2026-10-09, before a compact, on the user's request. The buffer beside this file holds the standing state: rulings in the user's words, method, orientation, ledger, candidates. This snapshot carries what the buffer does not: where the work stands this minute, what the hand knows, what will slip first, and the reasoning and corrections that shaped the stretch since the migration into this folder on 2026-10-01.

## Where it stands right now

- **A run is live in this repository.** `uv run orchestrator implement .` started on 2026-10-09. `27.1` (sleep prevention survives a soft stop) landed as `fd0f326`. `25.1.1` was in plan review at the last check. `25.1.2` and `25.2` follow in the same run, then Phase 26's header with no tasks, then the first `---STOP---`.
- **This snapshot and the buffer edit made with it are uncommitted while that run is live.** The orchestrator runs `git add -A` before its verify step, so they ride into `25.1.1`'s task commit and into the diff its code reviewer reads. The user was told. The fix is a Roadmap-update commit before `25.1.1` reaches verify, and the commit is the user's call.
- **Phase 26** ("A completion signal is recognized one way") is outlined only. It needs the deep pass and decomposition before a run can execute it.
- **Phase 27** sits directly after `24.2`, ahead of Phases 25 and 26. The user moved it there: «перенеси таски на 138 строку, слишком далеко в готовые закопал их». A live defect goes next to the seam, not into its thematic direction far up the file.

## Next action

1. Make `address.md` true again: probe for the session id, then take the session name from `ListAgents`. The name changes whenever the chat is reopened, and that happened on 2026-10-09.
2. Re-read the buffer.
3. Check the live run: `git log --oneline` for task commits, and the `.ai-factory/plans/trickster77777/` sidecars for `25.1.x`.
4. For each landed task, verify the commit against its spec: `0062` for `25.1.1`, `0060` for `25.1.2`, `0061` for `25.2`. If the run escalated, read the `## Escalation` section in the artifact. Do not pre-empt an escalation by editing a queued spec while the run is live.
5. When the user asks, take Phase 26 through deep and decompose.

## What the hand knows (recovery note — never sent to the editor)

The editor `a2e072d9ff36712d1` has been alive since 2026-09-08. It re-loaded `architect-editor-engine` and reads this buffer, and was given the buffer's path on 2026-10-05. Since then it wrote:
- `ARCHITECTURE.md`, twice: the Ports-and-Adapters rewrite, then `VerifyKind` and "a choice is held once";
- Phases 25, 26 and 27 and specs `0059`–`0063`;
- the doc edits in `pipeline.md`, `CLAUDE.md`, `test-mode.md`, `non-convergence.md`, `context-model.md` and `fault-handling.md`;
- the deletion of task 24.1, spec 57 and handoff 11 (2026-09-08);
- skills handoff 14.

Its pattern:
- **It slips on counts in "what is true now".** Three times: "in two functions", "its two callers", "each of the three". Every spec or preamble it writes gets a scan for number words.
- **Twice it wrote "full text printed above" without printing it.** Read every spec on the file yourself.
- **It catches what I miss and flags rather than forcing:**
  - the `## Deferred observations` "last line" clause in `pipeline.md`;
  - the third count in `0061`;
  - the test hazard in `0063`: the signal must not end pytest or its parent;
  - the contradiction between my own self-verify check and its guardrail.

## Reasoning that shaped this stretch

- **Architecture.** Skills 07 showed that `ARCHITECTURE.md` was the size-matrix output ("Team size: 1 developer → Layered"). The user ordered a rewrite by hand. My first Phase 25 design put `make_verifier` beside `verify_step`: one choice held twice. 07 caught it, and so did I, a step behind. I offered a test to pin the pairing. The user: «закрыть двойной инвариант тестом - ты как буд то предлагаешь поставить костыль тэстом в самом оркестраторе». The fix is design: `VerifyKind` holds everything that depends on the choice, the implementations read their signal from their kind, and 25.1 splits into the record (`25.1.1`) and the port (`25.1.2`). The factory taking the per-task `PlannerReviewer` stayed. The user called it an honest trade, because the reviewer is the planner's live session.
- **The experiment.** The user spawned head 02 to see whether the skeleton lens finds the double hold on its own. It did not; it found the doc propagation (`test-mode.md`) and a preamble-versus-spec wording mismatch. While 02's read was pending I held mine, and told 02 to go first rather than lie or hint. 07's analysis: `polymorphism-philosophy`'s time entry lets a pass stop at "a seam was cut".
- **Signal recognition.** Checking `PLAN_REVIEW_PASS` exposed a decision that never propagated. Commit `a236d77` replaced `endswith()` with `_has_signal`, which accepts an exact line among the last five, but only in `agents.py`. The user kept the tolerance: «возможно … не наш стиль». Docs first, then Phase 26.
- **Tools.** I told 07 that pipeline agents have only file and shell tools. That was wrong. Under `--dangerously-skip-permissions`, `--allowedTools` restricts nothing. I tested it with a headless agent using the pipeline's exact flags; it sent this session a message. I corrected the claim to 07. I also withdrew "Edit was meant to be absent", which was an intent read off a list.
- **The implementer's roadmap pointer.** I first called it a divergence from `context-model.md`. The user said it was deliberate. History confirmed it: `392d81b` gave the pointer on purpose, and the doc written later omitted it. The doc now states it.
- **Interviews.** Seven implementer interviews, on `--resume … --fork-session` copies with tools disallowed:
  - none of the seven opened the roadmap;
  - two opened the spec, both because their plan cited it;
  - their answers split on whether plan or spec wins.

  Then ten interviews on the escalated tasks from skills' rescue reports. I found the sessions by searching transcripts for writes that carry `## Escalation`. Every escalation was legitimate. The root causes:
  - specs that pinned literal code, or wrote "nothing breaks", without walking the code;
  - `planner.md`'s "note assumptions" line letting planners plan past contradictions;
  - an unwritten order of authority.

  07 later checked the record: pin-gaps did run on those tasks, missed every hole, and twice wrote the defect in itself. My prompt proposals (authority in `escalation.md`, the `planner.md` split, DEVIATION versus ESCALATION) were all rejected by the ruling below.
- **The ruling that closes the stretch.** «Задача оркестратора - выполнять таски, а не проверять их валидность. Эскалация сейчас работает как надо». Then: «глобальный клодмд - часть всей нашей системы». Never argue duplication into the orchestrator again. Validity is fixed where tasks are made, on the skills side.
- **The caffeinate defect,** relayed by 07 from core 130. Verified in code: `caffeinate` sits in the terminal's process group and dies at the first Ctrl+C, the soft stop. The fix combines both options, a new session plus `-w <pid>`, because a new session alone would orphan the assertion after a forced kill. Phase 27 went docs first.

## Corrections from the user this stretch, in his words

- «буфер не засоряй» — keep the buffer lean; a chronology belongs in a snapshot or nowhere.
- «оркестратор … обязан служить эталоном» — design over tests.
- «я не хочу, что б оркестратор читал всю документацию, когда этого не нужно для выполнения таска».
- «глобальный клодмд - часть всей нашей системы».
- «перенеси таски на 138 строку».
- «да не только в фазе! роадмап в принципе так устроен», relayed by 07. It is now the standing entry "a task's now".

## What must not be resolved by inference

- **Whether to touch `implementer.md`, `planner.md` or `escalation.md`.** It is ruled out. Raise it only if the user does.
- **Whether a skills-side change has landed.** Phase 77 (the "a task's now" seed entry), the commission gate in skills handoff 14, and the global CLAUDE.md sentence on where a task spec stands all live in the skills repo. Ask 07, at the name in skills `.ai-factory/architects/07/address.md`; never read its buffer.
- **Head 02's state** (folder 02 in this repo). Ask it; never read its buffer.

## Team

- **Above: skills 07, the liaison.** It sends behaviour and defect reports here; I verify each against the code before acting.
- **Peer: head 02** in this repository.
- **Below:** no one.
