from __future__ import annotations

from datetime import datetime, timezone
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
            draft_bytes = _render_draft_bytes(extraction)
            draft_hash = hashlib.sha256(draft_bytes).hexdigest()
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
            from .vault import Vault as _Vault
            _Vault._atomic_write(
                path.with_name(path.name + ".draft"), draft_bytes.decode("utf-8"),
            )
            current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            store.register_review(
                review.id, review.session_id, review.project, path,
                current_hash, draft_hash=draft_hash,
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


def _render_draft_bytes(extraction) -> bytes:
    """Render the same bytes Vault._render would produce, for hashing."""
    from .vault import Vault
    from .domain import ReviewStatus

    draft = ReviewDraft.model_construct(
        id="draft-stub",
        session_id="draft-stub",
        project="draft-stub",
        status=ReviewStatus.DRAFT,
        extraction=extraction,
        evidence=[],
        source_hash=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return Vault._render(draft).encode("utf-8")
