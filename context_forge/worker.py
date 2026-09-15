from __future__ import annotations

from pathlib import Path
import hashlib

from .domain import EventType, LlmGateway, ReviewDraft, ReviewExtraction, SessionEvent
from .gateways import NoOpGateway, OfflineGateway, select_gateway
from .queue import JobStore
from .vault import Vault


def process_one(store: JobStore, vault: Vault,
                gateway: LlmGateway | None = None) -> bool:
    """Process a single queued job; returns True if a job was handled.

    When the event is `session_end`, any open rule hits for the same
    session get a default `unknown` feedback so the auto-collected
    evidence exists before the user has a chance to override it.
    """
    job = store.claim()
    if job is None:
        return False
    gw = gateway or NoOpGateway()
    try:
        event = SessionEvent.model_validate_json(job["payload_json"])
        extraction = gw.extract_review(
            event.transcript_path, event.transcript_hash, event.session_id,
        )
        # Re-run domain validators so gateways that bypass Pydantic at
        # construction time still have to satisfy the contract (e.g. facts
        # without evidence_ids cannot land in accepted knowledge).
        extraction = ReviewExtraction.model_validate(extraction.model_dump())
        if extraction.should_save:
            review = ReviewDraft(
                id=f"review_{event.session_id}",
                session_id=event.session_id,
                project=event.project,
                source_hash=event.transcript_hash,
                extraction=extraction,
            )
            path = vault.write_review(review)
            store.register_review(
                review.id, review.session_id, review.project, path,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        if event.event_type is EventType.SESSION_END:
            store.auto_record_feedback_for_session(event.session_id)
        store.finish(job["id"])
    except Exception as exc:
        store.finish(job["id"], error=f"{type(exc).__name__}: {exc}")
        raise
    return True


__all__ = [
    "NoOpGateway",
    "OfflineGateway",
    "process_one",
    "select_gateway",
]
