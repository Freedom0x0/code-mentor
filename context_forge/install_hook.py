"""Install or remove the Claude Code hook for Context Forge.

Writes the SessionEnd and PreCompact entries into the user-level
`settings.json`. Idempotent: existing entries are not duplicated, and
running with `--uninstall` removes only the entries we own.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

HOOK_COMMAND = "python -m context_forge.hooks.claude_code"
HOOK_EVENTS = ("SessionEnd", "PreCompact")
HOOK_OWNER_KEY = "context_forge_managed"


def _settings_path(target: Path | None) -> Path:
    if target is not None:
        return target
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / "settings.json"


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def _owned_entries(hooks: list[dict]) -> list[dict]:
    return [h for h in hooks if isinstance(h, dict) and h.get(HOOK_OWNER_KEY)]


def install(target: Path | None = None) -> dict[str, int]:
    """Add the SessionEnd / PreCompact hooks to settings.json."""
    path = _settings_path(target)
    payload = _load(path)
    hooks_root = payload.setdefault("hooks", {})
    added = 0
    for event in HOOK_EVENTS:
        bucket = hooks_root.setdefault(event, [])
        if any(_owned_entries([h]) for h in bucket if isinstance(h, dict)):
            # Already installed; ensure no duplicate
            continue
        bucket.append({
            HOOK_OWNER_KEY: True,
            "hooks": [{
                "type": "command",
                "command": HOOK_COMMAND,
            }],
        })
        added += 1
    _save(path, payload)
    return {"added": added, "path": str(path)}


def uninstall(target: Path | None = None) -> dict[str, int]:
    """Remove only the Context Forge entries from settings.json."""
    path = _settings_path(target)
    payload = _load(path)
    hooks_root = payload.get("hooks", {})
    removed = 0
    for event in HOOK_EVENTS:
        bucket = hooks_root.get(event, [])
        kept = [h for h in bucket if not (isinstance(h, dict) and h.get(HOOK_OWNER_KEY))]
        removed += len(bucket) - len(kept)
        if kept:
            hooks_root[event] = kept
        else:
            hooks_root.pop(event, None)
    if not hooks_root:
        payload.pop("hooks", None)
    _save(path, payload)
    return {"removed": removed, "path": str(path)}
