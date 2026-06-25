## Plan Review: Caffeinate no-crash on non-macOS

**Plan:** `34-caffeinate-no-crash-on-non-macos.md`
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture (`ARCHITECTURE.md`):** PASS — change is confined to the orchestration layer (`main.py`), no layer-boundary or dependency-direction violations.
- **Rules (`RULES.md`):** Not present — skipped (WARN: optional file absent, non-blocking).
- **Roadmap (`ROADMAP.md`):** PASS — milestone "Caffeinate no-crash on non-macOS" exists and the plan's intent matches the roadmap description verbatim (wrap `Popen` in `try/except FileNotFoundError`, no macOS behavior change).

### Codebase Verification
- `_with_caffeinate` is at `main.py:396-416` — the plan's "~line 396-416" is exact.
- Current spawn is `subprocess.Popen(["caffeinate", "-ims"])` at line 398 — matches the plan.
- Return value is consumed as `time_str` in `run_implement` (line 721) and `run_test` (line 730), then printed. The plan correctly requires the non-macOS branch to return the same formatted elapsed string, preserving callers.
- `signal` and `subprocess` are already imported and used in this module — no new imports required for the macOS branch; the non-macOS branch needs neither.

### Critical Issues
None.

### Observations (non-blocking)
- The existing code has a latent inconsistency the plan should not propagate: the `except Exception` branch (lines 404-406) computes an `hours`-aware `elapsed_str`, and the success branch (lines 413-416) also does. The plan's instruction to "factor it so there is no duplication divergence" is the right call and will tidy this up. Recommend the shared helper compute the `"{hours}h {mins}m {secs}s"` / `"{mins}m {secs}s"` string from a single `start`, used by both branches and both the macOS and non-macOS paths.
- Detection of non-macOS is correctly keyed on `FileNotFoundError` (binary absent) rather than `sys.platform`. This is more robust — it also handles macOS systems where `caffeinate` is somehow unavailable, and a non-macOS host that happens to have a `caffeinate` shim still works. Good choice; no change needed.
- Minor: `caffeinate.wait()` in the existing `finally` can momentarily block on SIGTERM handling, but that behavior is unchanged by this plan and out of scope.

### Positive Notes
- Scope is tight and surgical — single function, single file, no API or signature changes.
- Settings (no tests, minimal logging, no docs) are appropriate for a small platform-compatibility hardening fix.
- The plan explicitly mandates "no behavior change on macOS" and pins the exact return-string format, which removes ambiguity for the implementer.

PLAN_REVIEW_PASS
