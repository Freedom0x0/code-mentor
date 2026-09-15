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

    Recognised names follow the §21 contract: `offline`, `fake`,
    `local`, `remote`. Anything else collapses to `NoOpGateway` so
    unconfigured deployments still let capture / vault / search run.
    """
    name = (provider or "").strip().lower()
    if name == "offline":
        return OfflineGateway()
    if name == "fake":
        return FixtureGateway(_fixture_extraction())
    if name == "local":
        return NoOpGateway()  # local model client is a deployment choice
    if name == "remote":
        return NoOpGateway()  # remote model client is a deployment choice
    return NoOpGateway()


def _fixture_extraction() -> ReviewExtraction:
    """Default fixture used when `provider = "fake"`."""
    return ReviewExtraction(
        title="fixture session",
        problem="placeholder problem",
        outcome="fixture gateway did not run a model",
        reason="fixture gateway",
        should_save=False,
    )


class FixtureGateway:
    """Returns caller-supplied ReviewExtractions.

    Used to verify that the worker honours structured constraints. A
    fixture that emits a fact claim without `evidence_ids` must fail
    the job (see §24 case 4).
    """

    def __init__(self, fixture: ReviewExtraction) -> None:
        self.fixture = fixture
        self.name = "fixture"

    def extract_review(self, transcript_path, transcript_hash, session_id):
        return self.fixture

    def compile_rule(self, knowledge_id, knowledge_text):
        return RuleExtraction(instruction=knowledge_text.strip()[:400])
