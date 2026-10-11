"""The verify port and the verify-kind type: what a verify step does, and everything that depends on which one runs."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, NamedTuple, Protocol


class VerifierProtocol(Protocol):
    """Given the plan and output path, write the verify artifact and report pass or fail by its completion signal."""

    def verify(self, plan_path: Path, out_path: Path, prev_out_path: Path | None) -> bool: ...


class VerifyKind(NamedTuple):
    """Everything that depends on the verify choice (review vs. test run)."""
    step: str
    fail_tag: str
    output_dirname: str
    output_suffix: str  # artifact tail with an {n} placeholder, e.g. "-review-{n}.md"
    pass_signal: str
    running_header: str
    pass_line_label: str
    fail_line_label: str
    max_iterations_message: str  # template with {n}, {path}, {content} placeholders
    make_verifier: Callable[[VerifierProtocol, Path], VerifierProtocol]  # (reviewer, project_dir) -> verifier
