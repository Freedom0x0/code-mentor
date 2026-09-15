from __future__ import annotations

from pathlib import Path
import hashlib

from .config import load_settings
from .domain import EventType, LlmGateway, ReviewDraft, ReviewExtraction, SessionEvent
from .gateways import NoOpGateway, OfflineGateway, select_gateway
from .queue import JobStore
from .vault import Vault


def process_one(store: JobStore, vault: Vault,
                gateway: LlmGateway | None = None,
                max_attempts: int | None = None) -> bool:
    """Process a single queued job; returns True if a job was handled.

    When the event is `session_end`, any open rule hits for the same
    session get a default `unknown` feedback so the auto-collected
    evidence exists before the user has a chance to override it.
    """
    job = store.claim()
    if job is None:
        return False
    gw = gateway or NoOpGateway()
    if max_attempts is None:
        settings = load_settings()
        max_attempts = settings.max_attempts if settings else 3
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
            # Stash the original draft next to the file so `review-diff`
            # can show what the user changed without re-running the model.
            # The draft is byte-identical to what we just wrote, so the
            # diff only ever surfaces the user's edits.
            from .vault import Vault as _Vault
            _Vault._atomic_write(
                path.with_name(path.name + ".draft"),
                path.read_text(encoding="utf-8"),
            )
            current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            store.register_review(
                review.id, review.session_id, review.project, path,
                current_hash,
                draft_hash=current_hash,
            )
        if event.event_type is EventType.SESSION_END:
            store.auto_record_feedback_for_session(event.session_id)
        store.finish(job["id"], max_attempts=max_attempts)
    except Exception as exc:
        store.finish(job["id"], error=f"{type(exc).__name__}: {exc}",
                     max_attempts=max_attempts)
    return True


__all__ = [
    "NoOpGateway",
    "OfflineGateway",
    "process_one",
    "select_gateway",
]
