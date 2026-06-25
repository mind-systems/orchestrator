# Code Review: Caffeinate no-crash on non-macOS

## Scope
Changes to `orchestrator/main.py`: extraction of `_fmt_elapsed` helper and hardening of `_with_caffeinate` against a missing `caffeinate` binary.

## Verification against the plan
- `subprocess.Popen(["caffeinate", "-ims"])` is now wrapped in `try/except FileNotFoundError`. ✓
- macOS path (Popen succeeds) is behaviorally identical to the original: run `func`, on exception print the elapsed line and re-raise, `finally` sends `SIGTERM` and `wait()`s, then returns the formatted elapsed string. ✓
- Non-macOS path (`FileNotFoundError`) runs `func` directly with no caffeinate process management, preserves the same `>>> Ran for ...` error path before re-raising, and returns the same formatted elapsed string. ✓
- Elapsed-formatting logic is factored into a single `_fmt_elapsed` helper, eliminating duplication. ✓

## Correctness analysis
- Only `FileNotFoundError` is caught around `Popen`; any real runtime error from `func` still propagates as before. Correct — the fix is narrowly scoped to the missing-binary case.
- In the `FileNotFoundError` branch no `caffeinate` variable is created, and the branch returns before reaching the `finally` block that references it, so there is no `NameError`/unbound-variable risk.
- `start = time.monotonic()` is now captured before the `Popen` call rather than after. The timing delta is sub-millisecond and, if anything, slightly more accurate; no functional impact.
- `_fmt_elapsed` reproduces the original formatting exactly (`{h}h {m}m {s}s` when hours, else `{m}m {s}s`); both the success returns and the error-path prints route through it consistently.
- No new imports needed; `time`, `subprocess`, `signal` are already imported and still used.

No bugs, security issues, or correctness problems found.

REVIEW_PASS
