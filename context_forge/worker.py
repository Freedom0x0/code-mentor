"""Worker: claim a job, extract session artifacts, write 3 vault files.

The auto-loop is intentional: worker calls the model, gets one
`SessionArtifacts` per session, and writes:

  vault/_drafts/{session_id}.md              archival of model output
  vault/knowledge/accepted/{k_id}.md       auto-published knowledge
  vault/rules/proposals/rule-{k_id}.md     proposed rule candidate

User actions are file-based, never command-based: edit, archive,
or change frontmatter `status`. `user_owned: true` blocks auto-
overwrite of hand-written entries.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .config import load_settings
from .domain import (
    EventType,
    LlmGateway,
    SessionArtifacts,
    SessionEvent,
)
from .gateways import NoOpGateway, select_gateway
from .queue import JobStore
from .vault import Vault


def _sigterm_to_keyboard_interrupt(signum, frame):  # noqa: ARG001
    raise KeyboardInterrupt


def process_one(store: JobStore, vault: Vault,
                gateway: LlmGateway | None = None,
                max_attempts: int | None = None) -> bool:
    """Process a single queued job. Returns True if a job was handled.

    Side effects on success:
    - vault/_drafts/{session_id}.md written (archival)
    - vault/knowledge/accepted/{k_id}.md if knowledge is non-null
    - vault/rules/proposals/rule-{k_id}.md if rule_candidate is non-null

    Files flagged `user_owned: true` are skipped (not overwritten).
    """
    from . import status as status_mod

    job = store.claim()
    if job is None:
        return False
    gw = gateway or NoOpGateway()
    if max_attempts is None:
        settings = load_settings()
        max_attempts = settings.max_attempts if settings else 3
    try:
        event = SessionEvent.model_validate_json(job["payload_json"])
        artifacts = gw.extract_session(
            event.transcript_path, event.transcript_hash, event.session_id,
        )
        # Re-run domain validators so gateways that bypass Pydantic at
        # construction time still have to satisfy the contract.
        artifacts = SessionArtifacts.model_validate(artifacts.model_dump())
        if artifacts.should_save:
            _write_session_artifacts(vault, event, artifacts)
        if event.event_type is EventType.SESSION_END:
            store.auto_record_feedback_for_session(event.session_id)
        store.finish(job["id"], max_attempts=max_attempts)
    except Exception as exc:
        store.finish(job["id"], error=f"{type(exc).__name__}: {exc}",
                     max_attempts=max_attempts)
    finally:
        try:
            status_mod.write_status_file(
                status_mod.status_path(),
                status_mod.collect(store),
            )
        except Exception:
            pass
    return True


def _write_session_artifacts(vault: Vault, event: SessionEvent,
                              artifacts: SessionArtifacts) -> None:
    """Write the archival draft + knowledge + rule candidate.

    Each write is best-effort: a single failure (e.g. user-owned file)
    must not block the other writes.
    """
    try:
        vault.write_draft(event.session_id, artifacts)
    except Exception as exc:
        print(f"[worker] draft write failed for {event.session_id}: {exc}")

    if artifacts.knowledge is not None:
        try:
            vault.write_knowledge_auto(
                event.session_id, artifacts.knowledge, artifacts,
            )
        except FileExistsError as exc:
            # user_owned file -- skip, do not overwrite
            print(f"[worker] knowledge skip: {exc}")
        except Exception as exc:
            print(f"[worker] knowledge write failed: {exc}")

    if artifacts.rule_candidate is not None and artifacts.knowledge is not None:
        try:
            vault.write_rule_candidate(
                event.session_id,
                artifacts.knowledge.id,
                event.project,
                artifacts.rule_candidate,
            )
        except FileExistsError as exc:
            print(f"[worker] rule skip: {exc}")
        except Exception as exc:
            print(f"[worker] rule write failed: {exc}")


def run_loop(store: JobStore, vault: Vault,
             gateway: LlmGateway | None = None,
             interval_seconds: float = 2.0,
             max_attempts: int = 3,
             stop_after: int | None = None) -> int:
    """Long-running worker. `stop_after` lets tests terminate cleanly."""
    import signal
    import time
    try:
        signal.signal(signal.SIGTERM, _sigterm_to_keyboard_interrupt)
    except (AttributeError, ValueError):
        pass
    processed_total = 0
    print(f"[worker] loop started; interval={interval_seconds}s "
          f"max_attempts={max_attempts}")
    try:
        while True:
            try:
                processed = process_one(store, vault, gateway, max_attempts)
            except Exception as exc:  # noqa: BLE001
                print(f"[worker] loop error: {type(exc).__name__}: {exc}")
                processed = False
            if processed:
                processed_total += 1
                if stop_after is not None and processed_total >= stop_after:
                    break
            else:
                if stop_after is not None and processed_total >= stop_after:
                    break
                time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("[worker] interrupted; exiting")
    return processed_total


__all__ = [
    "NoOpGateway",
    "process_one",
    "run_loop",
    "select_gateway",
]
