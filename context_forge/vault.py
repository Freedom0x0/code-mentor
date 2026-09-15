from __future__ import annotations

import datetime as _dt
import hashlib
import os
import re
import tempfile
from pathlib import Path

from .domain import ReviewDraft
from .index import parse_frontmatter, write_index


class Vault:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe(self, relative: str) -> Path:
        target = (self.root / relative).resolve()
        if target != self.root and self.root not in target.parents:
            raise ValueError("path escapes vault root")
        return target

    def write_review(self, review: ReviewDraft) -> Path:
        slug = re.sub(r"[^a-z0-9-]+", "-", review.extraction.title.lower()).strip("-") or review.id
        target = self._safe(f"reviews/{review.created_at:%Y}/{review.created_at:%Y-%m-%d}-{slug}.md")
        target.parent.mkdir(parents=True, exist_ok=True)
        content = self._render(review)
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != hashlib.sha256(content.encode()).hexdigest():
            raise FileExistsError(f"document conflict: {target}")
        return self._atomic_write(target, content)

    def list_reviews(self) -> list[Path]:
        return sorted(self.root.glob("reviews/**/*.md"))

    def list_knowledge(self, status: str | None = None) -> list[Path]:
        pattern = f"status: {status}" if status else None
        results: list[Path] = []
        for path in sorted(self.root.glob("knowledge/**/*.md")):
            if pattern is None:
                results.append(path)
                continue
            front, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
            if front.get("status") == status:
                results.append(path)
        return results

    def accept_knowledge(self, knowledge_id: str) -> Path:
        """Move a proposal to `knowledge/accepted/` and flip status.

        If the proposal carries a `candidate_instruction` field, also
        seed a matching `RuleProposal` so the user can enable a rule
        directly from accepted knowledge (§11 second-slice precursor).
        """
        source = self._find_knowledge(knowledge_id, statuses=("proposed", "accepted"))
        if source is None:
            raise FileNotFoundError(f"knowledge proposal not found: {knowledge_id}")
        text = source.read_text(encoding="utf-8")
        front, _ = parse_frontmatter(text)
        accepted = re.sub(r"(?m)^status:\s*[^\n]+$", "status: accepted", text, count=1)
        if "status:" not in accepted:
            raise ValueError(f"knowledge file has no status field: {source}")
        target = self._safe(f"knowledge/accepted/{knowledge_id}.md")
        target.parent.mkdir(parents=True, exist_ok=True)
        if source == target:
            result = source
        else:
            result = self._atomic_write(target, accepted)
            source.unlink()
        instruction = front.get("candidate_instruction", "").strip()
        project = front.get("candidate_project", front.get("project", "")).strip()
        paths_raw = front.get("candidate_paths", "")
        paths = [p.strip() for p in paths_raw.split(",") if p.strip()]
        if instruction and project:
            try:
                self.write_rule_proposal(
                    knowledge_id=knowledge_id,
                    project=project,
                    instruction=instruction,
                    paths=paths,
                )
            except FileExistsError:
                # an existing proposal is fine — the user already has a draft
                pass
        return result

    def _find_knowledge(self, knowledge_id: str,
                        statuses: tuple[str, ...] = ()) -> Path | None:
        for path in sorted(self.root.glob(f"knowledge/**/{knowledge_id}.md")):
            if not statuses:
                return path
            front, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
            if front.get("status") in statuses:
                return path
        return None

    def update_with_expected_hash(self, relative: str, content: str,
                                  expected_hash: str) -> Path:
        """Write `content` to `relative` only if the current file's hash matches.

        If the file changed under us, write a `.conflict-<ts>` copy instead
        of overwriting the user's edits and report the original path.
        """
        target = self._safe(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            current_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            if current_hash != expected_hash:
                stamp = _dt.datetime.now().strftime("%Y%m%d%H%M%S")
                conflict = target.with_suffix(target.suffix + f".conflict-{stamp}")
                conflict.write_text(content, encoding="utf-8", newline="\n")
                raise FileExistsError(
                    f"vault file changed; conflict copy at {conflict}"
                )
        return self._atomic_write(target, content)

    def scan(self) -> dict[str, int]:
        """Rebuild the FTS index and regenerate the auto-owned index.md.

        Markdown remains the source of truth. SQLite content is wiped and
        re-populated; index.md is overwritten because it is a generated nav.
        """
        from .index import DocumentIndex

        DocumentIndex(self._index_path()).rebuild(self.root)
        write_index(self.root)
        return {"files": self._count_markdown(), "index": 1}

    def _count_markdown(self) -> int:
        return sum(1 for _ in self.root.rglob("*.md") if _.name != "index.md")

    def _index_path(self) -> Path:
        import hashlib
        key = hashlib.sha256(str(self.root).encode("utf-8")).hexdigest()[:16]
        return Path.home() / ".context-forge" / f"index-{key}.db"

    @staticmethod
    def _atomic_write(target: Path, content: str) -> Path:
        fd, temp_name = tempfile.mkstemp(prefix=".forge-", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return target

    def write_knowledge_proposal(self, review_id: str, review_path: Path) -> Path:
        """Derive a knowledge proposal from a review file.

        The proposal's frontmatter is rebuilt from scratch so we don't carry
        over stale `status:` or `session_id:` fields from the review. Body
        content is preserved.
        """
        _, body = parse_frontmatter(review_path.read_text(encoding="utf-8"))
        target = self._safe(f"knowledge/proposals/{review_id}.md")
        target.parent.mkdir(parents=True, exist_ok=True)
        new_front = (
            "---\n"
            "type: knowledge\n"
            f"id: {review_id}\n"
            "status: proposed\n"
            f"created_at: {_dt.datetime.now(_dt.timezone.utc).isoformat()}\n"
            "---\n\n"
        )
        content = new_front + body.rstrip() + "\n"
        if target.exists():
            if target.read_text(encoding="utf-8") == content:
                return target
            raise FileExistsError(f"knowledge proposal conflict: {target}")
        return self._atomic_write(target, content)

    def write_rule_proposal(self, knowledge_id: str, project: str, instruction: str,
                            paths: list[str] | None = None) -> Path:
        rule_id = f"rule-{knowledge_id}"
        target = self._safe(f"rules/proposals/{rule_id}.md")
        target.parent.mkdir(parents=True, exist_ok=True)
        path_lines = "\n".join(f"  - {path}" for path in (paths or [])) or "  []"
        content = ("---\n" "type: rule\n" f"id: {rule_id}\n"
                   f"source_knowledge_id: {knowledge_id}\n" f"project: {project}\n"
                   "status: proposed\n" "paths:\n" f"{path_lines}\n" "---\n\n"
                   f"{instruction.strip()}\n")
        if target.exists():
            if target.read_text(encoding="utf-8") != content:
                raise FileExistsError(f"rule proposal conflict: {target}")
            return target
        return self._atomic_write(target, content)

    def set_rule_status(self, rule_id: str, status: str) -> Path:
        matches = list(self.root.glob(f"rules/**/{rule_id}.md"))
        if not matches:
            raise FileNotFoundError(f"rule not found: {rule_id}")
        target = matches[0]
        content = target.read_text(encoding="utf-8")
        updated = re.sub(r"(?m)^status:\s*[^\n]+$", f"status: {status}", content, count=1)
        if updated == content:
            raise ValueError(f"rule has no status field: {target}")
        target.write_text(updated, encoding="utf-8", newline="\n")
        return target

    @staticmethod
    def _render(review: ReviewDraft) -> str:
        e = review.extraction
        lines = ["---", "type: review", f"id: {review.id}", f"project: {review.project}",
                 f"session_id: {review.session_id}", f"status: {review.status}",
                 f"created_at: {review.created_at.isoformat()}", "---", "", f"# {e.title}", "",
                 "## 问题", "", e.problem or "（未提取）", "", "## 尝试", ""]
        for attempt in e.attempts:
            lines.append(f"- {attempt.summary}：{attempt.result}")
        lines += ["", "## 结果", "", e.outcome or "（未提取）", "", "## Claims", ""]
        for claim in e.claims:
            lines.append(f"- [{claim.kind}] {claim.text} (evidence: {', '.join(claim.evidence_ids) or 'none'})")
        lines += ["", "## 不确定性", ""] + [f"- {item}" for item in e.uncertainties]
        return "\n".join(lines).rstrip() + "\n"
