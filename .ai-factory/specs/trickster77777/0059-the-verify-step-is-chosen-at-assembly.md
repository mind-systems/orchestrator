# What diverges now: the verify choice is held in many places and decided inside the flow

**Date:** 2026-10-05
**Source:** the user's go in chat on 2026-10-05 for closing "one choice held twice" by design, under `.ai-factory/ARCHITECTURE.md`

Governing spec: [ARCHITECTURE.md](../../ARCHITECTURE.md).

The architecture says the verify kind is one record, `VerifyKind`, beside its implementations, holding everything that depends on the choice; that the mode record holds that kind; that the verify step is a port, `VerifierProtocol`, whose implementation the kind's factory builds; and that the flow never asks which mode it runs in — [What varies](../../ARCHITECTURE.md), [Composition root](../../ARCHITECTURE.md), [The rule](../../ARCHITECTURE.md). The code is not yet that:

- **`process_task` in `orchestrator/main.py` decides the verify implementation itself.** It reads `mode.verify_step`: on the test-run value it builds a `TestRunner`, and its local `_verify` closure then calls that runner or `planner_reviewer.review`; on the review value it looks up the previous review file so the reviewer can see it. The mode tag is a question the flow asks, which the rule forbids.
- **The verify choice is held across sibling values with nothing tying them.** `Mode` carries `verify_step`, `verify_fail_tag`, `output_dirname`, `output_suffix`, `pass_signal` and the run's verify wording (`verify_running_header`, `pass_line_label`, `fail_line_label`, `max_iterations_message`) as separate fields. `_detect_task_step` and `_detect_test_task_step` in `orchestrator/resume.py` restate the step name, failure tag, output suffix and pass signal as literals for `_detect_step`. `PlannerReviewer.review` in `orchestrator/agents.py` writes `REVIEW_PASS` into its composed prompt sentences and checks for that literal, and `TestRunner` appends the literal `TEST_PASS`. Nothing makes any pairing among them agree.
- **`Mode` carries no verify implementation and no verify kind**, so `_implement_loop` and `_test_loop` have nothing to hand the flow beyond a bag of strings, and `VerifierProtocol` and `VerifyKind` do not exist.
- **The per-roadmap artifact subdirectory is joined by hand where directories are built:** in `process_task` onto its plans, output and plan-reviews directories, and in `_run_dynamic_loop` onto its plans directory again. The architecture derives every artifact directory from the subdirectory in one place.
