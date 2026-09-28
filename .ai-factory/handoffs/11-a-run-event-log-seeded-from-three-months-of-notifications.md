# Handoff — a run-event log, seeded from three months of notifications

**Processed:** `[ ]` — whoever reads this marks it; a marked handoff is spent.

> Architect-side handoff from a session in `~/projects/sakshi/skills`, 2026-09-09. Three months of this orchestrator's Telegram notifications were recovered, classified, and written out as an append-only run-event log. Two untracked files are waiting in this repository. What is asked of this repository is one thing: make the orchestrator append to that log itself, in the same format, so effectiveness stays measurable for years instead of for as long as a chat history survives.

## What arrived, and where it is

Two files, both untracked, both in this repository:

- `scripts/tg_effectiveness.py` — reads a Telegram Desktop export (JSON or HTML), classifies every terminal notification, and either prints an analysis or writes the event log. Standard library only.
- `metrics/runs.jsonl` — the seed: **203 events, 23 June to 9 September 2026**, one JSON object per line, oldest first.

Commit them or move them as you see fit. The path `metrics/runs.jsonl` was chosen so that nothing in `.ai-factory/` owns it — the log must outlive every prune, and it spans every project this orchestrator runs, so it cannot live inside any one project's tree.

## The format, which is the contract

One JSON object per line. Append-only. Not a JSON array — an array cannot be appended to without rewriting the whole file, and a run interrupted mid-write would destroy every earlier record.

```
{"v":1,"ts":"2026-09-09T11:17:08","project":"skills","outcome":"run_done",
 "tasks_done":7,"elapsed_s":6029,"stage":null,"reason":null,"source":"telegram-export"}
```

- `v` — schema version, currently `1`. A later shape bumps it; readers branch on it and old lines keep parsing.
- `ts` — ISO 8601. Seed rows have no offset: the export does not carry one. Rows this orchestrator writes should carry a full offset, which is why the field is a string and not an epoch.
- `project` — the project directory's name, exactly as the notification already reports it.
- `outcome` — a closed set: `run_done`, `task_done`, `failure`, `halt`, `manual`, `force_quit`, `error`, `escalation`. These map one-to-one onto the outcomes the notifier already distinguishes.
- `tasks_done`, `elapsed_s` — integers, or `null`.
- `stage` — for a failure only: `plan_review`, `review`, or `implement`. Reconstructed from the reason text in the seed; this orchestrator knows it first-hand and should write it directly.
- `reason` — the failure or halt text, verbatim.
- `source` — `telegram-export` for the seed, `orchestrator` for anything this repository writes.

### Three decisions worth not undoing

**`null` is not `0`.** Seventy-two of the 203 seed rows carry `tasks_done: null`, because the run summary did not exist in the notification format until part-way through July. Writing zero there would have made a June with no measurement look like a June with no work, and any average taken years later would inherit the lie silently. The same holds forward: a field that was not measured is null.

**`source` exists because provenance decays.** The seed is reconstructed from message text, and its classification is inference — good inference, but inference. Rows this orchestrator writes are first-hand. In a year nothing else will distinguish them.

**`stage` is the field the whole log was built for.** See below.

## What is asked of this repository

The notifier's `report()` is already the single point every terminal event passes through, and it already receives everything the record needs — the outcome, the project, the detail line, and the run summary carrying elapsed time and task count. Appending a line there is a small addition beside the send.

One condition that is easy to miss: **the append must not be subject to the alert filter.** Notifications are filtered by configured alert type, and the per-task alert is currently disabled — which is precisely why three months of history contains no task-level success events and the seed has to infer task counts from run summaries. The log should record every terminal event regardless of what is sent to Telegram. The two concerns are different: one is what the operator wants to be interrupted by, the other is what the record must contain.

Beyond that: nothing. No new dependency — the file is a line of JSON and an open in append mode. No schema negotiation — the format above is fixed and versioned.

## What the seed already says

Ninety-four failures across the three months. Their stages:

| stage | failures |
|---|---|
| `plan_review` | 73 |
| `review` | 18 |
| `implement` | 3 |

**Ninety-one of ninety-four failures happen before any code is written.** The pipeline almost never fails at implementation; it exhausts itself deciding what to implement. That single ratio is the reason this log is worth keeping — it is the number to watch move, and it was invisible until three months of messages were read as a series.

Two projects account for most of it, and they are the two whose task specifications were written in the heaviest style; two others in the same period ran at eight and thirty-five tasks per failure. That is a correlation and is offered as one, not as a cause.

## The seed's limits, so nobody over-reads it

- **June carries no task counts at all** — the run summary was not in the format yet. June rows are real events with `tasks_done: null`. Any per-task metric must exclude them rather than treat them as zero.
- **July is partial** — 24 of its 127 messages predate the summary.
- **August and September are complete.**
- The notification format changed three times over the window, including the milestone-to-task rename. The classifier recognises all three generations; a fourth will need it taught.
- One first line, `Orchestrator stopped`, covers two different outcomes — a run that exhausted its review budget and a run stopped by a usage threshold. Only the reason line separates them. A failure is a verdict on the work; a halt is not, and averaging them together would be the easiest way to make this log say nothing.

## What not to do

Do not backfill the seed with guesses, and do not rewrite its rows: it is a record of what was recoverable, and its gaps are part of what it records. Do not convert the file to a JSON array. Do not let the log inherit the notification filter. And if a later format change makes an old row ambiguous, bump `v` for new rows rather than editing old ones — a log edited in place stops being evidence.
