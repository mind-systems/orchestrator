# Architect buffer — head 01, orchestrator

## Editor handle

- `a2e072d9ff36712d1` — agent type `editor`, spawned in this session (see `address.md`). Message it with `SendMessage`; the next channel-message is the liveness probe. It has **not yet been told** this buffer's path — see the Ledger.

## Team

- **Above:** `skills`, folder 07. Per that head, the user made this head its liaison into the orchestrator: the skills side hands behaviour over before it lands in the skills, and it is tried in the field here. Confirmed by the user in this chat on 2026-10-01: «да всё ништяк».
- **Below:** none.

## Where things stand

- The architect memory moved into `.ai-factory/architects/01/` on the user's instruction: the buffer from `.ai-factory/notes/01-architect-buffer.md`, and snapshot `10-fault-reporting-and-the-operator-surface.md` from `.ai-factory/handoffs/`. The move is staged as renames and **not committed** — the user asked for no commit.
- No unit of work is in flight here. The orchestrator roadmap has nothing open above its first `---STOP---`; the Phase 24 that stands there now is a different phase from the one deleted in this session (see Orientation).
- Two proposals from this session wait on the user's go, nothing more: the commission gate (skills side) and the escalation pair (this side). Both are under "Candidates — not tasks".

## Rulings in force

- **The heads talk to each other directly, inside the family.** In the user's words: «дальше мы - искусственный интеллект и разговариваем внутри сакши». A peer head in `sakshi` is reached with `SendMessage` at the name in its folder's `address.md` and answered there; the user is not the relay between heads. Approval of edits and commits still stays in each head's own chat.

- **A task carries everything the run must read.** In the user's words: «Таск должен быть написан самодостаточно. Всё что оркестратору надо читать - должно быть в таске … а не просить оркестратора читать там и тут и вообще прочитать всё и сделать для себя новый таск». A spec that points across a boundary for the very fact it implements, and forbids restating it, leaves the run to invent its own task. *Drains to:* the skills-side decomposition discipline (`roadmap-decompose` / `roadmap-engine`), not to anything in this repository.

## Method

**Standing entry — the counts rule.** A number someone decided is written:
it stays true however the tree grows. A measurement of the current tree is
not written, dated or not — write what produces it, the rule or the search
that gives it fresh each time. A spec least of all carries a number
measuring the tree: tasks run one after another, and each one changes the
tree the next was written against, so such a number in a queued spec is
false before the orchestrator reaches it, and the orchestrator cannot
execute a spec whose facts no longer hold. A number met in a spec, a plan or
a report is read as an order of magnitude; one that has gone stale is not a
defect to correct, count again or stop on. Two counts that disagree are not
reconciled against each other; ask which member is missing.

**Standing entry — what a spec holds.** A spec states what is true now,
what must be true after and what breaks on contact, and nothing else. It
carries no check that the instruction was carried out: the orchestrator
plans, builds and reviews on its own, and a check written into a spec comes
back as plan steps and review rounds. It names no position in a file, only
what the artifact must hold. It puts no fence around a neighbour; scope is
what the task changes.

**Standing entry — state the behaviour and stop.** A rule says what happens
and ends there: no sentence for each case it excludes, no guard against its
own misuse. A rule or a fix that needs guards against its own machinery is
the wrong one.

**Standing entry — a task is not retold in the code.** A spec's reasons are
for whoever plans, and the code keeps none of them. A task says what must be
true and what to delete or link; it never asks for a comment carrying its
reasoning, a skeleton's contract or its scope. A comment in code says only
what a reader would get wrong from the code alone, where the reader meets
it, in a line or three.

**Standing entry — the orchestrator's commit takes the whole tree.** While
it runs a queue in a repository, leave nothing uncommitted there, or it
lands inside a task's commit.

**Ask whether the task was ordered before repairing it.** When the user pushes back on a task, the first question is whether anyone commissioned the behaviour, not how to make the task sounder. Every gate the family owns checks a task's form, so a well-grounded repair to an unordered task produces a better task that still should not exist — and only the user's question stops it.

**An empty result from a path that does not exist reads as "no".** A grep against a wrong path returns the same silence as a grep whose answer is no, and the conclusion it seems to support can even be right by accident. Open the path before trusting an empty result; across the family, skills live under `skills/src/skills/<name>/SKILL.md`, not under `src/commands/`.

**A self-verify check is derived against the tree it will run in.** A check carried over from an earlier round, or drafted fast, can contradict the order's own guardrails — "no changed tracked files" in an order that also forbids touching a file already modified. It has failed twice across sessions; it is a debt against the work-order guidance, not yet drained.

**A `cd` inside a compound command leaks into the next check of the same call.** Address another repository with `git -C <path>` or absolute paths, never by changing directory mid-command. It has failed twice in one session, once on each side of the pair; also a debt not yet drained.

**Work deleted before its first commit leaves no history.** A count of deletions taken from `git log -p` sees only what was once committed, and mostly sees `[ ]` → `[x]` transitions and retitles. The cost of unordered tasks killed in the working tree cannot be measured from either repository.

## Orientation

- **`note`'s template states provenance as a constant.** Its `**Source:**` line is a literal, `conversation context`, not a placeholder, and `roadmap-engine` delegates the task-spec format to `note` — so nearly every task spec carries a field that looks like a commission and never asked for one. A pre-filled field silences the question an absent one would raise.
- **No gate in the family asks whether a task was commissioned.** The two-tier shape, the contract-line budget, pinned values, the Atomicity Gate, pin-gaps — all are gates on form. pin-gaps does carry a docs branch ("behavior the task assumes that no document states"), but it audits a task's content, never its existence; a reader finding that branch will wrongly conclude the case is covered.
- **"Ground truth wins over the plan" has no counterpart for a governing spec.** That rule in `implementer.md`'s Critical Rules is right for a plan and wrong for a document: a governing spec outranks the code, so a disagreement there must stop the run. Without the counterpart, a run reconciles in the wrong direction — task 21.3's commit `8bef0c5` rewrote invariant 5 of `docs/concepts/fault-handling.md`, which its own spec named only as source and never asked to change.
- **The family-root path convention does not reach a run.** The root `CLAUDE.md` lets a sub-repo artifact name its sibling root-relative from the family root; that holds for a reader standing at the family root. An orchestrator agent is launched with its working directory at the target project, so such a path in a task spec resolves to nothing during the run.
- **Task number 24.1 here names two different tasks over time.** The phase-note task deleted on 2026-09-08 (spec 57, handoff 11, both gone) and the landed "No agent is offered work that outlives its turn". Skills `.ai-factory/handoffs/14-the-task-nobody-ordered.md` and this folder's history mean the deleted one. The spec-number gap at 57 is permanent.
- **The orchestrator roadmap has two `---STOP---` markers.** The first is the seam.
- **Snapshot 10 still names the buffer's old path** in its read map. It is a record and stays as written; the buffer lives here now.

## Ledger

- **Tell the editor where this buffer lives.** *What:* the hand has never been given this buffer's path — it was spawned under the older rule that kept the buffer private. *Why deferred:* the path rides inside a channel-message already being sent, never in a message of its own, and none is pending. *Trigger:* the next channel-message to the editor, which carries `.ai-factory/architects/01/buffer.md` alongside its payload.
- **A task spec's paths must resolve from the run's own working directory.** *What:* every agent the orchestrator launches gets `cwd=str(self.project_dir)` in `agents.py`, so a cross-repo path written root-relative from the family root resolves to nothing in a run, against `docs/concepts/context-model.md`'s commitment that "the contract line is the only guaranteed entry point". *Why deferred:* the one task that broke it was deleted, nothing is wrong today, and the rule's home is the skills-side decomposition discipline rather than this repository. *Trigger:* the next task here whose spec names a path outside this repository, or any session working on decomposition rules on the skills side.

## Candidates — not tasks

- **The commission gate (skills repository).** Make a task's commission an answered question at decomposition instead of `note`'s constant: either in `note`'s template, which also shapes handoffs and research notes, or as a per-entry gate in `roadmap-decompose` beside the Atomicity Gate, or both. Handed off in full as skills `.ai-factory/handoffs/14-the-task-nobody-ordered.md`; not built as of 2026-10-01. *Promotes on:* the user's go and their choice of landing.
- **The escalation pair (this repository).** Extend `escalation.md`'s "the ratified spec above the current task" from a fork the spec leaves open to a spec that contradicts the task's target behaviour or does not cover it; and give `implementer.md`'s "Ground truth wins over the plan" its counterpart — for a governing spec, the spec wins and the run stops. Lower yield than the gate by the user's own symptom: it catches a run editing its spec, not a planner writing an unordered task. *Promotes on:* the user's go.
- **The pipeline asks an architect (observation from skills 07, kept watched, not queued).** Design in `skills/docs/future/the-pipeline-asks-an-architect.md`: at `ESCALATION` the agent sends its task's contact architect one line pointing at where the question sits, and does not wait. Here it needs `SendMessage` on the agents' allowed-tools list in `agents.py`, which today holds only file and shell tools. It also meets `docs/concepts/fault-handling.md`'s rule that a notification never says where to find the account — the clause a run wrote unordered in task 21.3. The doorbell is a peer message, not an operator notification, but the docs would have to say so before it lands. *Promotes on:* the user deciding to touch the prompts.
- **The pipeline generates its own repair (observation from skills 07, kept watched, not queued).** `reviewer.md`'s "Deferred observations criterion" makes anything fixable inside the task a finding "down to cosmetics", `REVIEW_PASS` needs zero findings, and everything outside the task becomes a deferred observation that the skills-side prune routes into a phase. Fix-phases grow with the work done. The commission gate would not stop this: every such task carries a real source, a reviewer's observation. *Promotes on:* the user deciding to touch the prompts.
- *Considered and dropped:* forbidding a plan to list any `docs/` path its spec does not name — too blunt; it would have blocked task 8.1, whose spec names `docs/*.md` by glob.

## Current thread

The user's stated position on documentation, in their words: «Иногда оркестратору надо дать доступ менять доки и абсолютный запрет даже не понятно как сформулировать. Но и логика в том, что дай ему писать документацию - и мы получаем поведение, которое ни кто не заказывал». My read: the cut is authorship, not the directory — a run changes a document only where its spec pins the change, and an unpinned doc edit is an escalation. But the user's actual symptom — a week of deleting unordered tasks — enters a level higher, at decomposition, which is why the commission gate outranks the escalation pair. The open fork on the gate is its tier: `note` is a general distiller with several callers, so a requirement placed there lands on handoffs too.
