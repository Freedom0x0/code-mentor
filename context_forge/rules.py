from __future__ import annotations

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
    matches one segment without separators. Other characters match
    literally.
    """
    import re
    regex_parts = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                if i + 2 < len(pattern) and pattern[i + 2] == "/":
                    regex_parts.append(r"(?:.*/)?")
                    i += 3
                    continue
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


_LIST_KEYS = {"paths", "sources", "topics"}


def _frontmatter(content: str) -> tuple[dict[str, object], str]:
    if not content.startswith("---\n"):
        return {}, content
    marker = content.find("\n---", 4)
    if marker < 0:
        return {}, content
    values: dict[str, object] = {}
    for line in content[4:marker].splitlines():
        if not line.strip() or line.startswith(" ") or line.startswith("\t"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in _LIST_KEYS and value and "," in value:
            values[key] = [v.strip() for v in value.split(",") if v.strip()]
        else:
            values[key] = value
    return values, content[marker + 4:].strip()


class RuleMatcher:
    def __init__(self, vault_root: Path):
        self.root = vault_root.resolve()

    def match(self, project: str, changed_path: str | None = None) -> list[RuleMatch]:
        matches: list[RuleMatch] = []
        for path in self.root.glob("rules/**/*.md"):
            metadata, instruction = _frontmatter(path.read_text(encoding="utf-8"))
            if metadata.get("status") != "enabled":
                continue
            if metadata.get("project") != project:
                continue
            patterns = metadata.get("paths", [])
            if isinstance(patterns, str):
                patterns = [patterns]
            if not patterns:
                if changed_path is None:
                    matches.append(RuleMatch(
                        str(metadata.get("id", path.stem)), path,
                        f"project={project}", instruction,
                    ))
                continue
            if changed_path and any(glob_match(changed_path, p) for p in patterns):
                matches.append(RuleMatch(
                    str(metadata.get("id", path.stem)), path,
                    f"project={project}, path={changed_path} matches "
                    f"{', '.join(patterns)}",
                    instruction,
                ))
        return matches
