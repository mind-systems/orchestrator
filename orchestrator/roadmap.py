"""Parse and update .ai-factory/ROADMAP.md files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

CHECKBOX_RE = re.compile(r"^- \[([ x])\] \*\*(.+?)\*\*\s*[—–-]\s*(.+)$")


@dataclass
class Milestone:
    title: str
    description: str
    done: bool
    line_number: int  # 0-based line index in file

    @property
    def slug(self) -> str:
        """Convert title to a filename-safe slug."""
        s = self.title.lower()
        s = re.sub(r"[^a-z0-9]+", "-", s)
        return s.strip("-")


def parse_roadmap(path: Path) -> list[Milestone]:
    """Parse ROADMAP.md and return list of milestones."""
    lines = path.read_text().splitlines()
    milestones: list[Milestone] = []

    for i, line in enumerate(lines):
        m = CHECKBOX_RE.match(line.strip())
        if m:
            done = m.group(1) == "x"
            title = m.group(2).strip()
            description = m.group(3).strip()
            milestones.append(Milestone(title=title, description=description, done=done, line_number=i))

    return milestones


def mark_done(path: Path, milestone: Milestone) -> None:
    """Mark a milestone as completed in ROADMAP.md."""
    lines = path.read_text().splitlines()
    line = lines[milestone.line_number]
    lines[milestone.line_number] = line.replace("- [ ]", "- [x]", 1)
    path.write_text("\n".join(lines) + "\n")


def mark_skipped(path: Path, milestone: Milestone) -> None:
    """Mark a milestone as skipped (already done) in ROADMAP.md."""
    lines = path.read_text().splitlines()
    line = lines[milestone.line_number]
    lines[milestone.line_number] = line.replace("- [ ]", "- [x] ⚠️ SKIPPED (already implemented)", 1)
    path.write_text("\n".join(lines) + "\n")
