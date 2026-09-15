"""LlmGateway implementations.

The MVP only ships the offline and no-op gateways. Local and remote providers
remain a deployment choice and must be plugged in behind the same Protocol.
"""

from __future__ import annotations

from pathlib import Path

from .domain import LlmGateway, ReviewExtraction, RuleExtraction
from .transcript import sanitize_transcript


class OfflineGateway:
    """Offline reviewer that only inspects sanitized transcript structure.

    Used as the default and as the test fixture. Never produces fact claims,
    so the resulting ReviewDraft cannot be auto-promoted to accepted knowledge.
    """

    name = "offline"

    def extract_review(self, transcript_path: str | None,
                       transcript_hash: str | None,
                       session_id: str) -> ReviewExtraction:
        if not transcript_path:
            return ReviewExtraction(
                title=f"Session {session_id}",
                reason="no transcript_path",
                should_save=False,
            )
        sanitized = sanitize_transcript(Path(transcript_path))
        lines = [line.strip() for line in sanitized.content.splitlines() if line.strip()]
        return ReviewExtraction(
            title=f"Session {session_id}",
            problem=lines[0][:500] if lines else "",
            outcome="offline gateway did not run a model",
            reason="offline gateway",
            should_save=bool(lines),
        )

    def compile_rule(self, knowledge_id: str, knowledge_text: str) -> RuleExtraction:
        return RuleExtraction(instruction=knowledge_text.strip()[:400])


class NoOpGateway:
    """Used when the user has not configured a model provider.

    Lets capture, vault and search keep working without any model call.
    """

    name = "none"

    def extract_review(self, transcript_path: str | None,
                       transcript_hash: str | None,
                       session_id: str) -> ReviewExtraction:
        return ReviewExtraction(
            title=f"Session {session_id}",
            reason="model provider not configured",
            should_save=False,
        )

    def compile_rule(self, knowledge_id: str, knowledge_text: str) -> RuleExtraction:
        return RuleExtraction(instruction=knowledge_text.strip()[:400])


def select_gateway(provider: str) -> LlmGateway:
    """Map a settings-level provider name to a gateway implementation.

    Anything other than `offline` collapses to `NoOpGateway` because the
    MVP has no model client yet. This keeps the LLM boundary optional.
    """
    if provider == "offline":
        return OfflineGateway()
    return NoOpGateway()
