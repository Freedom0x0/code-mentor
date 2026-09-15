"""HTTP-backed LlmGateway implementations.

`RemoteGateway` talks to the Anthropic Messages API; `LocalGateway` talks
to an Ollama-compatible `/api/chat` endpoint. Both share `HttpGateway`
which owns HTTP plumbing, retry/backoff and JSON parsing.

The provider is pluggable: when the user sets `model_provider = "remote"`
or `"local"` and supplies credentials, the worker will actually call the
model. Without credentials the gateway is skipped and the system keeps
working — capture / vault / search remain usable.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any

from .domain import LlmGateway, ReviewExtraction, RuleExtraction


_PROMPT = (
    "You are reviewing a sanitized Claude Code session transcript. "
    "Reply with strict JSON only — no prose, no markdown fences — that "
    "matches this schema:\n"
    "{{"
    "\"title\": string, "
    "\"problem\": string, "
    "\"attempts\": [{{\"summary\": string, \"result\": string, "
    "\"evidence\": [string]}}], "
    "\"outcome\": string, "
    "\"claims\": [{{\"text\": string, \"kind\": \"fact|inference|open_question\", "
    "\"confidence\": \"low|medium|high\", \"evidence_ids\": [string]}}], "
    "\"uncertainties\": [string], "
    "\"candidate_topics\": [string], "
    "\"should_save\": boolean, "
    "\"reason\": string"
    "}}\n"
    "Facts MUST cite at least one evidence id. Open questions and "
    "inferences can omit evidence. Set should_save=false if the session "
    "lacks an actionable lesson.\n\n"
    "Transcript (sanitized):\n{transcript}\n"
)


@dataclass
class _CallResult:
    text: str
    attempts: int


class GatewayError(RuntimeError):
    """Raised by HTTP gateways when the model is unreachable or misbehaves."""


class HttpGateway:
    """HTTP + retry + JSON plumbing shared by RemoteGateway and LocalGateway."""

    name = "http"

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0,
                 timeout: float = 30.0) -> None:
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.timeout = timeout
        self._client = None  # lazy: tests inject a MockTransport

    def _client_instance(self):
        if self._client is None:
            import httpx
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def _post(self, url: str, headers: dict[str, str],
              body: dict[str, Any]) -> _CallResult:
        import httpx

        client = self._client_instance()
        last_exc: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = client.post(url, headers=headers, json=body)
            except httpx.HTTPError as exc:
                last_exc = exc
                self._sleep_backoff(attempt)
                continue
            if response.status_code in {429, 500, 502, 503, 504}:
                last_exc = GatewayError(
                    f"{response.status_code} {response.reason_phrase}"
                )
                self._sleep_backoff(attempt)
                continue
            if response.status_code >= 400:
                raise GatewayError(
                    f"{response.status_code} {response.text[:200]}"
                )
            text = response.text
            return _CallResult(text=text, attempts=attempt)
        raise GatewayError(f"max attempts exhausted: {last_exc}")

    def _sleep_backoff(self, attempt: int) -> None:
        delay = self.base_delay * (2 ** (attempt - 1))
        time.sleep(min(delay, 8.0))

    @staticmethod
    def _parse_json_object(text: str) -> dict[str, Any]:
        """Extract the first JSON object from a model reply.

        Tolerates surrounding prose and trailing text. Uses
        `raw_decode` so nested objects do not derail extraction the way
        `text.find('{')` + `rfind('}')` does.
        """
        decoder = json.JSONDecoder()
        idx = text.find("{")
        while idx >= 0:
            try:
                obj, _end = decoder.raw_decode(text[idx:])
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                pass
            idx = text.find("{", idx + 1)
        raise GatewayError(f"model returned no JSON object: {text[:120]}")

    @staticmethod
    def _transcript_excerpt(transcript_path: str | None,
                             transcript_hash: str | None) -> str:
        if not transcript_path:
            return f"(no transcript; hash={transcript_hash or 'unknown'})"
        from .transcript import sanitize_transcript
        sanitized = sanitize_transcript(__import__("pathlib").Path(transcript_path))
        body = sanitized.content.strip()
        if len(body) > 8000:
            body = body[:8000] + "\n... (truncated)"
        return body or "(empty)"

    def extract_review(self, transcript_path, transcript_hash, session_id):
        excerpt = self._transcript_excerpt(transcript_path, transcript_hash)
        prompt = _PROMPT.format(transcript=excerpt)
        reply = self._call_chat(prompt)
        data = self._parse_json_object(reply)
        # Re-validate via the domain model so any contract drift is caught.
        return ReviewExtraction.model_validate(data)

    def compile_rule(self, knowledge_id, knowledge_text):
        prompt = (
            "Distill the following knowledge into a single-sentence rule "
            "instruction and a comma-separated list of glob patterns. "
            "Reply with strict JSON only: "
            "{\"instruction\": string, \"paths\": [string]}\n\n"
            f"Knowledge id: {knowledge_id}\n{knowledge_text}"
        )
        reply = self._call_chat(prompt)
        data = self._parse_json_object(reply)
        return RuleExtraction.model_validate(data)

    # subclasses override
    def _call_chat(self, prompt: str) -> str:
        raise NotImplementedError


class RemoteGateway(HttpGateway):
    """Anthropic Messages API.

    Requires `remote_api_key` in settings. Falls back to NoOpGateway when
    absent so unconfigured deployments still run.
    """

    name = "remote"

    def __init__(self, api_url: str, api_key: str, model: str,
                 max_attempts: int = 3) -> None:
        super().__init__(max_attempts=max_attempts)
        if not api_key:
            raise GatewayError("remote_api_key is empty")
        self.api_url = api_url.rstrip("/") + "/v1/messages"
        self.api_key = api_key
        self.model = model

    def _call_chat(self, prompt: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        result = self._post(self.api_url, headers, body)
        try:
            payload = json.loads(result.text)
        except json.JSONDecodeError as exc:
            raise GatewayError(f"anthropic returned non-JSON: {exc}") from exc
        blocks = payload.get("content") or []
        texts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
        return "\n".join(texts)


class LocalGateway(HttpGateway):
    """Ollama-compatible /api/chat endpoint."""

    name = "local"

    def __init__(self, api_url: str, model: str,
                 max_attempts: int = 3) -> None:
        super().__init__(max_attempts=max_attempts)
        self.api_url = api_url.rstrip("/") + "/api/chat"
        self.model = model

    def _call_chat(self, prompt: str) -> str:
        headers = {"content-type": "application/json"}
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
        }
        result = self._post(self.api_url, headers, body)
        try:
            payload = json.loads(result.text)
        except json.JSONDecodeError as exc:
            raise GatewayError(f"local model returned non-JSON: {exc}") from exc
        message = payload.get("message") or {}
        return message.get("content", "")


def build_remote(api_key: str | None = None, model: str | None = None,
                 api_url: str | None = None) -> LlmGateway:
    """Factory honouring environment overrides for the remote gateway.

    Reads env vars in this order:
    - key:  `ANTHROPIC_API_KEY` → `ANTHROPIC_AUTH_TOKEN` (Claude Code)
    - url:  `ANTHROPIC_API_URL` → `ANTHROPIC_BASE_URL` (Claude Code)
    - model: `ANTHROPIC_MODEL`  → `ANTHROPIC_DEFAULT_SONNET_MODEL`
                            → `ANTHROPIC_DEFAULT_OPUS_MODEL`
                            → `ANTHROPIC_DEFAULT_HAIKU_MODEL`
    """
    key = (
        api_key
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        or ""
    )
    url = (
        api_url
        or os.environ.get("ANTHROPIC_API_URL")
        or os.environ.get("ANTHROPIC_BASE_URL")
        or "https://api.anthropic.com"
    )
    chosen = (
        model
        or os.environ.get("ANTHROPIC_MODEL")
        or os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL")
        or os.environ.get("ANTHROPIC_DEFAULT_OPUS_MODEL")
        or os.environ.get("ANTHROPIC_DEFAULT_HAIKU_MODEL")
        or "claude-3-5-sonnet-20241022"
    )
    if not key:
        raise GatewayError(
            "ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN not set"
        )
    return RemoteGateway(api_url=url, api_key=key, model=chosen)


def build_local(model: str | None = None,
                api_url: str | None = None) -> LlmGateway:
    url = api_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    chosen = model or os.environ.get("OLLAMA_MODEL", "llama3")
    return LocalGateway(api_url=url, model=chosen)
