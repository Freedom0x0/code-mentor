from __future__ import annotations

from pathlib import Path
import hashlib

from .domain import LlmGateway, ReviewDraft, SessionEvent
from .gateways import NoOpGateway, OfflineGateway, select_gateway
from .queue import JobStore
from .vault import Vault


def process_one(store: JobStore, vault: Vault,
                gateway: LlmGateway | None = None) -> bool:
    """Process a single queued job; returns True if a job was handled."""
    job = store.claim()
    if job is None:
        return False
    gw = gateway or NoOpGateway()
    try:
        event = SessionEvent.model_validate_json(job["payload_json"])
        extraction = gw.extract_review(
            event.transcript_path, event.transcript_hash, event.session_id,
        )
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
        store.finish(job["id"])
    except Exception as exc:
        store.finish(job["id"], error=f"{type(exc).__name__}: {exc}")
    return True


__all__ = [
    "NoOpGateway",
    "OfflineGateway",
    "process_one",
    "select_gateway",
]
