from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from ..domain import EventType, SessionEvent
from ..queue import JobStore


def main() -> int:
    payload = json.load(sys.stdin)
    transcript = payload.get("transcript_path")
    transcript_hash = None
    if transcript and Path(transcript).is_file():
        transcript_hash = hashlib.sha256(Path(transcript).read_bytes()).hexdigest()
    cwd = payload.get("cwd") or str(Path.cwd())
    session_id = payload.get("session_id") or hashlib.sha256(
        f"{cwd}:{transcript or ''}".encode("utf-8")
    ).hexdigest()[:24]
    event_name = payload.get("hook_event_name", "SessionEnd")
    event = SessionEvent(
        event_id=hashlib.sha256(
            f"{session_id}:{event_name}:{transcript_hash}".encode("utf-8")
        ).hexdigest(),
        event_type=EventType.PRE_COMPACT if event_name == "PreCompact" else EventType.SESSION_END,
        source="claude_code",
        session_id=session_id,
        project=Path(cwd).name,
        cwd=cwd,
        transcript_path=transcript,
        transcript_hash=transcript_hash,
    )
    queued = JobStore(Path.home() / ".context-forge" / "queue.db").enqueue_event(event)
    print("queued" if queued else "duplicate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
