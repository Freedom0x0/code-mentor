from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EventType(StrEnum):
    SESSION_END = "session_end"
    PRE_COMPACT = "pre_compact"


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class RuleStatus(StrEnum):
    PROPOSED = "proposed"
    ENABLED = "enabled"
    DISABLED = "disabled"


class ClaimKind(StrEnum):
    FACT = "fact"
    INFERENCE = "inference"
    OPEN_QUESTION = "open_question"


class SessionEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_id: str = Field(min_length=1)
    event_type: EventType
    source: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    project: str = Field(min_length=1)
    cwd: str = Field(min_length=1)
    transcript_path: str | None = None
    transcript_hash: str | None = None
    occurred_at: datetime = Field(default_factory=utc_now)


class Evidence(BaseModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_line: int | None = Field(default=None, ge=1)


class Claim(BaseModel):
    text: str = Field(min_length=1)
    kind: ClaimKind
    confidence: str = "medium"
    evidence_ids: list[str] = Field(default_factory=list)


class Attempt(BaseModel):
    summary: str = Field(min_length=1)
    result: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)


class ReviewExtraction(BaseModel):
    title: str = Field(min_length=1)
    problem: str = ""
    attempts: list[Attempt] = Field(default_factory=list)
    outcome: str = ""
    claims: list[Claim] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    candidate_topics: list[str] = Field(default_factory=list)
    should_save: bool = True
    reason: str = ""

    @field_validator("claims")
    @classmethod
    def facts_need_evidence(cls, claims: list[Claim]) -> list[Claim]:
        for claim in claims:
            if claim.kind is ClaimKind.FACT and not claim.evidence_ids:
                raise ValueError("fact claims require evidence_ids")
        return claims


class ReviewDraft(BaseModel):
    id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    project: str = Field(min_length=1)
    status: ReviewStatus = ReviewStatus.DRAFT
    extraction: ReviewExtraction
    evidence: list[Evidence] = Field(default_factory=list)
    source_hash: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class RuleProposal(BaseModel):
    id: str = Field(min_length=1)
    source_knowledge_id: str = Field(min_length=1)
    project: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    status: RuleStatus = RuleStatus.PROPOSED
    paths: list[str] = Field(default_factory=list)


class EventEnvelope(BaseModel):
    event: SessionEvent
    received_at: datetime = Field(default_factory=utc_now)
    raw: dict[str, Any] = Field(default_factory=dict)


class RuleExtraction(BaseModel):
    """Structured output of `LlmGateway.compile_rule`."""

    instruction: str = Field(min_length=1)
    paths: list[str] = Field(default_factory=list)


class LlmGateway(Protocol):
    """Boundary that turns sanitized evidence into structured artifacts.

    A gateway must be cheap to call but never the source of truth for
    product state. It must never receive raw transcripts and must never
    return free-form text in place of a validated model.
    """

    name: str

    def extract_review(self, transcript_path: str | None,
                       transcript_hash: str | None,
                       session_id: str) -> ReviewExtraction: ...

    def compile_rule(self, knowledge_id: str, knowledge_text: str) -> RuleExtraction: ...
