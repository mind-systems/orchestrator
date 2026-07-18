# The `- Affects:` placeholder speaks task spec — emitter side of the lockstep pair

Phase 17 of the Reserved-words language conformance direction. Governing spec: [reserved-words](../../../../skills/docs/reserved-words.md). Task 7.1 (spec [26](26-prompt-bodies-speak-the-language.md)) conformed `reviewer.md`'s prose but froze the jointly-owned deferred-observations entry line byte-for-byte, recording that it "changes in lockstep or not at all". This is that lockstep change, planned as its own unit. The scanner side is skills task 17.5 (`skills/.ai-factory/specs/73-affects-placeholder-task-spec-path.md`); the two tasks run in parallel, in either order — neither touches the scanned bytes, and both pin the identical target field, so any execution order converges.

## Current state

`orchestrator/prompts/reviewer.md:108` instructs the reviewer to emit the deferred-observations entry as:

```
- Affects: <phase / spec-note path / "unknown"> — <one-paragraph observation>
```

The field placeholder carries the retired synonym `spec-note` (registry name: task spec). The scanner side (`skills/src/skills/orchestrator-artifacts/SKILL.md:55`) documents the same line with the same `spec-note path` field and the tail `<observation>` — the tails already differ between the sides, harmlessly: the bytes the skills scan are the `## Deferred observations` heading and the `- Affects: ` prefix, never the placeholder tail.

## Change

One field on one line — `reviewer.md:108`: `spec-note path` → `task-spec path`. Target line:

```
- Affects: <phase / task-spec path / "unknown"> — <one-paragraph observation>
```

The field string `<phase / task-spec path / "unknown">` is pinned identically in the skills-side spec — that shared pin, not execution order, is what makes the pair converge.

## Guards

- **Scanned literals byte-identical.** The `## Deferred observations` heading (`reviewer.md:106`) and the `- Affects: ` prefix are the bytes the skills scan — untouched.
- **The tail stays `— <one-paragraph observation>`.** It is a length instruction to the reviewer; the scanner side keeps its own `— <observation>` as a format description. A recorded per-side difference, not drift — both specs state it.
- **Parallel-safe.** Correct whether it lands before or after skills 17.5; no ordering constraint exists.
- **`PLAN_REVIEW_PASS` / `REVIEW_PASS` literals and the `Spec:` / `Governing spec:` tags untouched.**

## Verification

- `grep -n 'task-spec path' orchestrator/prompts/reviewer.md` → line 108 only.
- `grep -rn 'spec-note' orchestrator/ docs/ CLAUDE.md` → zero (frozen `.ai-factory/` history exempt).
- `grep -n '## Deferred observations\|- Affects:\|PLAN_REVIEW_PASS\|REVIEW_PASS' orchestrator/prompts/reviewer.md` → heading, prefix, and PASS literals byte-identical pre/post except the one field on line 108.
