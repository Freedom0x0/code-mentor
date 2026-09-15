from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SanitizedTranscript:
    source_path: Path
    source_hash: str
    content: str


_SECRET_PATTERNS = [
    (re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s\"']+"), r"\1[REDACTED]") ,
    (re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,\"']+"), r"\1=[REDACTED]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "[REDACTED:private_key]"),
    (re.compile(r"(?i)(postgres|mysql|mongodb)(://)[^\s\"']+"), r"\1\2[REDACTED]"),
]


def sanitize_transcript(path: Path) -> SanitizedTranscript:
    import hashlib

    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8", errors="replace")
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return SanitizedTranscript(path, digest, text)
