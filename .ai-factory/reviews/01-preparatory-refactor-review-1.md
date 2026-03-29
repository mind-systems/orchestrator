## Code Review Summary

**Files Reviewed:** 2 (`orchestrator/agents.py`, `orchestrator/main.py`)
**Risk Level:** 🟢 Low

### Context Gates
- **ARCHITECTURE.md:** WARN — file does not exist, no boundary rules to check.
- **RULES.md:** WARN — file does not exist, no convention rules to check.
- **ROADMAP.md:** OK — milestone "Preparatory refactor" is marked `[x]` done.

### Critical Issues
None.

### Suggestions
None.

### Positive Notes
- Parameter threading is complete with zero gaps. Every function that consumed `MAX_REVIEW_ITERATIONS` now accepts `max_review_iterations` and all eight caller→callee edges pass it through correctly.
- `PipelineStopError` follows the same pattern as `RateLimitError` — minimal exception class, caught in `cli()` with clean exit.
- Env var reads use sensible defaults (`"3"` and `"2"`) that match the original hardcoded values.
- The global constant was cleanly deleted with no stale references remaining in source code.

REVIEW_PASS
