# MCP transport for Context Forge

The optional MCP server (`context_forge.mcp_server`) ships five tools
listed in §15 of the technical design:

- `context_forge_search(query)` — FTS5 lookup over the vault.
- `context_forge_get(path)` — read a Markdown file (path-validated).
- `context_forge_pending_reviews()` — list drafts awaiting approval.
- `context_forge_match_rules(project, changed_path)` — explain rule hits.
- `context_forge_record_feedback(rule_id, outcome, note)` — log outcome.

The server uses stdio transport. It runs from the user shell with
`python -m context_forge.mcp_server` and never opens a network port.

## Claude Desktop

Add this block to `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "context_forge": {
      "command": "python",
      "args": ["-m", "context_forge.mcp_server"],
      "cwd": "/path/to/your/repo"
    }
  }
}
```

The `cwd` should point at the repository that contains `context_forge/`.
Claude Desktop will launch the server with that working directory so
that `_store` and `_vault` resolve to the right per-user locations.

## Claude Code

Add the same entry under `mcpServers` in `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "context_forge": {
      "command": "python",
      "args": ["-m", "context_forge.mcp_server"]
    }
  }
}
```

The MCP server shares the application service with the CLI — no
business logic is duplicated. The five tools are read-mostly: only
`context_forge_record_feedback` writes to SQLite. Approving knowledge
or enabling rules still requires the CLI so humans stay in the loop.

## Verifying the install

```bash
python -c "from context_forge.mcp_server import create_server; \
    srv = create_server(); print(sorted(srv._tool_manager._tools))"
```

Should print the five tool names above. If `mcp` is not installed,
install it with `pip install mcp` (already listed under
`[project.optional-dependencies]`).
