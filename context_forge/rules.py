from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    path: Path
    reason: str
    instruction: str


def glob_match(path_str: str, pattern: str) -> bool:
    """Match a path against a glob pattern.

    `**` matches zero or more path segments (including none); single `*`
    matches one segment without separators. Other characters match literally.
    """
    regex_parts = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                # `**/` matches zero or more segments (with trailing slash)
                if i + 2 < len(pattern) and pattern[i + 2] == "/":
                    regex_parts.append(r"(?:.*/)?")
                    i += 3
                    continue
                # `**` at end or without slash matches anything
                regex_parts.append(r".*")
                i += 2
                continue
            regex_parts.append(r"[^/]*")
            i += 1
        elif c == "?":
            regex_parts.append(r"[^/]")
            i += 1
        elif c in ".+(){}|^$\\":
            regex_parts.append(re.escape(c))
            i += 1
        else:
            regex_parts.append(re.escape(c))
            i += 1
    return re.fullmatch("".join(regex_parts), path_str) is not None


def _frontmatter(content: str) -> tuple[dict[str, str | list[str]], str]:
    if not content.startswith("---\n"):
        return {}, content
    marker = content.find("\n---", 4)
    if marker < 0:
        return {}, content
    values: dict[str, str | list[str]] = {}
    for line in content[4:marker].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    paths: list[str] = []
    in_paths = False
    for line in content[4:marker].splitlines():
        if line.strip() == "paths:":
            in_paths = True
            continue
        if in_paths and re.match(r"\s+-\s+", line):
            paths.append(re.sub(r"^\s+-\s+", "", line).strip())
        elif in_paths and line and not line.startswith(" "):
            in_paths = False
    if paths:
        values["paths"] = paths
    return values, content[marker + 4:].strip()


class RuleMatcher:
    def __init__(self, vault_root: Path):
        self.root = vault_root.resolve()

    def match(self, project: str, changed_path: str | None = None) -> list[RuleMatch]:
        matches: list[RuleMatch] = []
        for path in self.root.glob("rules/**/*.md"):
            metadata, instruction = _frontmatter(path.read_text(encoding="utf-8"))
            if metadata.get("status") != "enabled" or metadata.get("project") != project:
                continue
            patterns = metadata.get("paths", [])
            if isinstance(patterns, str):
                patterns = [patterns]
            if not patterns:
                reason = f"project={project}"
            if changed_path and any(glob_match(changed_path, pattern) for pattern in patterns):
                reason = f"project={project}, path={changed_path} matches {', '.join(patterns)}"
            else:
                continue
            rule_id = str(metadata.get("id", path.stem))
            matches.append(RuleMatch(rule_id, path, reason, instruction))
        return matches
