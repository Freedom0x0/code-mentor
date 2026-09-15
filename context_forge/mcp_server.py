from __future__ import annotations

import hashlib
from pathlib import Path

from .rules import RuleMatcher


def _store():
    from .cli import _store as cli_store
    return cli_store()


def _vault():
    from .cli import _vault as cli_vault
    return cli_vault()


def _index():
    from .cli import _index as cli_index
    return cli_index()


def create_server():
    """Create the optional MCP server; importing MCP remains a deployment choice."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("MCP support requires the optional mcp package") from exc

    server = FastMCP("context-forge")

    @server.tool()
    def context_forge_search(query: str) -> list[dict[str, str]]:
        return [dict(row) for row in _index().search(query)]

    @server.tool()
    def context_forge_pending_reviews() -> list[dict[str, str]]:
        return [dict(row) for row in _store().list_reviews()]

    @server.tool()
    def context_forge_get(path: str) -> str:
        target = (_vault().root / path).resolve()
        if target != _vault().root and _vault().root not in target.parents:
            raise ValueError("path escapes vault root")
        return target.read_text(encoding="utf-8")

    @server.tool()
    def context_forge_match_rules(project: str, changed_path: str = "") -> list[dict[str, str]]:
        return [
            {"rule_id": match.rule_id, "reason": match.reason, "instruction": match.instruction}
            for match in RuleMatcher(_vault().root).match(project, changed_path or None)
        ]

    @server.tool()
    def context_forge_record_feedback(rule_id: str, outcome: str, note: str = "") -> str:
        if outcome not in {"helpful", "harmful", "irrelevant", "unknown"}:
            raise ValueError("invalid feedback outcome")
        _store().add_rule_feedback(rule_id, outcome, note or None)
        return "recorded"

    return server


def main() -> None:
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
