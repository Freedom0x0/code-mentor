from __future__ import annotations

import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    vault_path: Path
    knowledge_dir: str = "context-forge"
    processing_mode: str = "redacted_model"
    model_provider: str = "none"
    poll_interval_seconds: int = Field(default=2, ge=1)
    max_attempts: int = Field(default=3, ge=1)
    retention_days: int = Field(default=30, ge=0)
    excluded_globs: list[str] = Field(default_factory=list)

    # remote (Anthropic Messages API)
    remote_api_url: str = "https://api.anthropic.com"
    remote_api_key: str = ""
    remote_model: str = "claude-3-5-sonnet-20241022"

    # local (Ollama-compatible /api/chat)
    local_api_url: str = "http://localhost:11434"
    local_model: str = "llama3"

    @property
    def root(self) -> Path:
        return (self.vault_path / self.knowledge_dir).resolve()

    def validate_vault(self) -> None:
        path = self.vault_path.expanduser().resolve()
        if not path.exists() or not path.is_dir():
            raise ValueError(f"vault_path is not an existing directory: {path}")


def default_settings_path() -> Path:
    return Path(os.environ.get("CONTEXT_FORGE_HOME", "~/.context-forge")).expanduser() / "config.toml"


def load_settings(path: Path | None = None) -> Settings | None:
    config_path = path or default_settings_path()
    if not config_path.exists():
        return None
    with config_path.open("rb") as handle:
        return Settings.model_validate(tomllib.load(handle))
