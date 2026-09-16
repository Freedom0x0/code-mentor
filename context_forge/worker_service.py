"""Install / remove a Windows Task Scheduler entry for the worker daemon.

Part of `forge install-hook`: after writing the Claude Code hooks,
we also register a logon-triggered task that runs `forge worker run`
in the background. This way the user never has to remember to start
the worker manually.

On non-Windows the helpers raise PlatformError.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


TASK_NAME = "ContextForgeWorker"
_TASK_DESC = "Context Forge: poll queue.db and auto-write knowledge/rules."


class PlatformError(RuntimeError):
    pass


def _task_command() -> str:
    """Build a command string that works across reboots.

    Prefers the `forge` entry-point; falls back to python -m when
    forge is not on PATH.
    """
    if shutil.which("forge") is not None:
        return f'cmd /c start /b forge worker run'

    # Fallback with absolute python path
    python = Path.home() / "AppData/Local/Programs/Python/Python312/python.exe"
    if not python.exists():
        # Try the launcher
        python = Path.home() / "AppData/Local/Microsoft/WindowsApps/python3.exe"
    if not python.exists():
        python = Path("python")  # last resort
    cmd = (
        f'cmd /c start /b {python} -m context_forge.cli worker run'
    )
    return cmd


def _schtasks(*args: str) -> str:
    """Run schtasks and return combined output."""
    if not shutil.which("schtasks"):
        raise PlatformError("schtasks not available (Windows only)")
    proc = subprocess.run(
        ["schtasks", *args],
        capture_output=True, text=True, check=False,
    )
    return (proc.stdout + proc.stderr).strip()


def install() -> dict[str, str]:
    """Create a logon-triggered scheduled task for the worker."""
    cmd = _task_command()
    _schtasks(
        "/Create", "/TN", TASK_NAME, "/TR", cmd,
        "/SC", "ONLOGON", "/RL", "LIMITED",
        "/IT", "/F",
        "/V1",  # Compatible with older Windows
    )
    return {"task": TASK_NAME, "command": cmd}


def uninstall() -> dict[str, str]:
    """Remove the scheduled task."""
    _schtasks("/Delete", "/TN", TASK_NAME, "/F")
    return {"task": TASK_NAME}


def status() -> dict[str, str]:
    """Query the task and return its status."""
    try:
        out = _schtasks("/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST")
    except RuntimeError as exc:
        return {"task": TASK_NAME, "status": str(exc)}
    return {"task": TASK_NAME, "status": out[:400]}