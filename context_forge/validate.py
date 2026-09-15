"""`forge validate` — vault self-check.

Read-only. Walks the vault and reports:
- files with unparseable frontmatter
- files with paths that escape the vault root (shouldn't happen)
- orphaned conflict copies
- rule files referencing unknown status values
- knowledge/rule files outside their canonical directories

Designed for CI / pre-commit use: exits non-zero when any issue is found.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .index import parse_frontmatter


@dataclass(frozen=True)
class Issue:
    severity: str  # "error" or "warning"
    path: str
    detail: str


_KNOWN_RULE_STATUS = {"proposed", "enabled", "verified", "stale", "disabled", "archived"}
_KNOWN_KNOWLEDGE_STATUS = {"proposed", "accepted", "revised", "conflicted", "archived"}
_KNOWN_REVIEW_STATUS = {"draft", "approved", "rejected", "superseded"}


def validate_vault(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    if not root.exists():
        issues.append(Issue("error", str(root), "vault root does not exist"))
        return issues

    canonical = root.resolve()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "index.md":
            continue
        # Identify markdown by content rather than suffix because conflict
        # copies end in `<ts>`, not `.md`.
        try:
            head = path.read_text(encoding="utf-8", errors="replace")[:4]
        except OSError:
            continue
        if not head.startswith("---\n"):
            continue
        rel = str(path.relative_to(root))
        # Path safety
        try:
            resolved = path.resolve()
        except OSError as exc:
            issues.append(Issue("error", rel, f"cannot resolve: {exc}"))
            continue
        if canonical not in resolved.parents and resolved != canonical:
            issues.append(Issue("error", rel, "path escapes vault root"))
            continue
        # Conflict copies are orphans once their source file is removed
        if ".conflict-" in path.name:
            stem_target = path.with_name(
                re.sub(r"\.conflict-\d{14}$", "", path.name)
            )
            if not stem_target.exists():
                issues.append(Issue(
                    "warning", rel,
                    f"conflict copy with no canonical source ({stem_target.name})",
                ))
            continue
        # Read & parse frontmatter
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(Issue("error", rel, f"cannot read: {exc}"))
            continue
        front, _body = parse_frontmatter(text)
        kind = front.get("type", "")
        status = front.get("status", "")
        if kind == "rule" and status not in _KNOWN_RULE_STATUS:
            issues.append(Issue("error", rel, f"unknown rule status: {status!r}"))
        elif kind == "knowledge" and status not in _KNOWN_KNOWLEDGE_STATUS:
            issues.append(Issue(
                "error", rel, f"unknown knowledge status: {status!r}"
            ))
        elif kind == "review" and status not in _KNOWN_REVIEW_STATUS:
            issues.append(Issue("error", rel, f"unknown review status: {status!r}"))
        # Canonical directory check
        if kind == "review" and "reviews/" not in rel:
            issues.append(Issue("warning", rel, "review outside reviews/"))
        if kind == "knowledge" and status == "accepted" and "/accepted/" not in rel:
            issues.append(Issue("warning", rel,
                                "accepted knowledge outside knowledge/accepted/"))
        if kind == "knowledge" and status == "proposed" and "/proposals/" not in rel:
            issues.append(Issue("warning", rel,
                                "proposed knowledge outside knowledge/proposals/"))
        if kind == "rule" and status == "enabled" and "/proposals/" in rel:
            # We don't move rules between dirs on enable; flag for human review
            issues.append(Issue("warning", rel,
                                "enabled rule still in proposals/"))
    return issues


def render(issues: list[Issue]) -> tuple[str, int]:
    lines: list[str] = []
    failed = 0
    for issue in issues:
        marker = "ERR " if issue.severity == "error" else "WARN"
        if issue.severity == "error":
            failed += 1
        lines.append(f"[{marker}] {issue.path}: {issue.detail}")
    lines.append("")
    lines.append(f"{len(issues) - failed}/{len(issues)} ok")
    return "\n".join(lines), failed
