# Test Pipeline Mode

**Date:** 2026-05-12
**Source:** conversation context — tradeoxy_core test coverage planning

## Key Findings

- The standard 4-agent implement pipeline (Plan → PlanReview → Implement → CodeReview) is not well-suited for writing tests — pass/fail is objective (`npm test` output), not a matter of code quality judgment.
- A dedicated `test` mode is needed: 3 agents, where the review phase is replaced by an actual test runner, and iteration is driven by real test output.
- This mode should be added to the orchestrator alongside `implement`, `implement-review`, and `refactor`.

## Details

### Why a Separate Pipeline

In the `implement` mode, the **CodeReview** agent judges correctness subjectively. For tests, correctness is binary — the test suite either passes or it doesn't. Running a real `npm test` (or equivalent) as the gate:
- Eliminates false `REVIEW_PASS` from a reviewer that can't actually run the code
- Makes iteration loops faster and more accurate
- Avoids the situation where a test is syntactically correct but tests the wrong invariant and the reviewer misses it

### Proposed Pipeline: `test` mode

```
PlannerReviewer.plan()
  └─► PlanReviewer.review_plan()  ×N  (FAIL → PlannerReviewer.plan() again)
        └─► Implementer.implement()
              └─► TestRunner.run()  ×N  (FAIL → Implementer.implement() again)
                    └─► mark_done() + git commit
```

Where `TestRunner` is NOT an LLM agent — it is a shell executor that:
1. Runs the test command (e.g. `npm test -- --testPathPattern={spec_file}`)
2. Captures stdout/stderr + exit code
3. Writes output to `.ai-factory/test-runs/{seq}-{slug}-test-{n}.txt`
4. Returns `REVIEW_PASS` if exit code is 0, otherwise returns the failure output

The Implementer then reads the test output file on the next iteration (same as it reads review files today) and fixes the failing tests.

### Key Differences from `implement` Mode

| Aspect | implement | test |
|--------|-----------|------|
| Review agent | LLM (PlannerReviewer) | Shell command (no LLM) |
| Pass signal | `REVIEW_PASS` in file | Exit code 0 from test runner |
| Failure context | LLM findings in review file | Raw `npm test` output |
| Speed per iteration | ~3–5 min (LLM review) | ~10–30 sec (test run) |

### Test Command

Must be configurable per project. Options:
1. Read from `.ai-factory/DESCRIPTION.md` (e.g. `test_command: npm test`)
2. Pass as CLI argument: `uv run orchestrator test /path/to/project --cmd "npm test"`
3. Fallback: detect from `package.json` scripts

For tradeoxy_core: `npm test -- --testPathPattern={spec_file} --passWithNoTests`

The `{spec_file}` should be derived from the milestone title/description — the planner should include the target spec file in the plan so the runner knows what to execute.

### Milestone Format for Test Tasks

Test milestones in ROADMAP.md should specify the target spec file clearly so the runner can scope the test command:

```
- [ ] **Tests: TradeAggregator** — Write unit tests for `src/candles/trade-aggregator.ts`
  covering [list of behaviors]. Target file: `src/candles/trade-aggregator.spec.ts`.
  Test command: `npm test -- --testPathPattern=trade-aggregator.spec`.
```

### CLI Command

```bash
uv run orchestrator test /path/to/project
```

Behavior:
- Reads ROADMAP.md, filters pending milestones (same as implement)
- Runs the test pipeline for each milestone
- Stops on test failure that exceeds `ORCHESTRATOR_MAX_ITERATIONS`
- Same `---STOP---` breakpoint support as other modes

### Agent Reuse

- **PlannerReviewer** — reuse as-is (writes the test file, reviews plan)
- **PlanReviewer** — reuse as-is (reviews the plan before implementation)
- **Implementer** — reuse as-is (writes test code, reads test output on fix iterations)
- **TestRunner** — new: thin shell wrapper, no LLM, just runs the command and captures output

### Implementation Notes

- `TestRunner` can be a simple class in `agents.py` with a `run(spec_file, output_path, cmd_template)` method — no `_run_claude()` call needed
- The output file written by `TestRunner` should mirror the structure of review files so the Implementer's prompt can reference it the same way it references code review files today
- `process_test_milestone()` in `main.py` — new function, parallel to `process_milestone()` and `process_refactor_milestone()`

## Open Questions

- Should the test runner run the full suite after each fix iteration (to catch regressions) or just the target spec file? Running full suite is safer but slower.
- Should plan review be skipped for test tasks to speed up the cycle? (Tests have lower blast radius than production code changes — a bad test just fails, it doesn't break production behavior.)
