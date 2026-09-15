# Context Forge

本地优先的"开发会话 → 可复用知识 → AI 规则"编译器。基于
`docs/technical-design-context-forge.md` 的设计，按 MVP 第一切片实现。

## 安装

```bash
git clone <repo>
cd code-mentor
python -m pip install -e .

# 可选：安装 MCP server 依赖
python -m pip install -e ".[mcp]"
```

## 配置

默认放在 `~/.context-forge/config.toml`：

```toml
vault_path = "C:/Users/you/Documents/Obsidian"
knowledge_dir = "context-forge"
processing_mode = "redacted_model"
model_provider = "offline"      # offline | fake | local | remote
poll_interval_seconds = 2
max_attempts = 3
retention_days = 30
excluded_globs = ["**/.env*", "**/.ssh/**", "**/*secret*"]

# 真实 provider 配置（model_provider = "remote" 时使用）
remote_api_url = "https://api.anthropic.com"
remote_api_key = ""             # 或环境变量 ANTHROPIC_API_KEY
remote_model = "claude-3-5-sonnet-20241022"

# 本地 provider 配置（model_provider = "local" 时使用）
local_api_url = "http://localhost:11434"
local_model = "llama3"
```

未配置 provider 时 `capture / vault / search` 仍然可用。

## Claude Code hook 接入

```bash
forge install-hook
# 撤销：forge install-hook --uninstall
```

会把 `SessionEnd` / `PreCompact` 钩子写入 `~/.claude/settings.json`，通过
`context_forge_managed` 标记，`--uninstall` 只卸自己装的钩子。

## 核心命令

```bash
# 1. 启动 worker（一次性）
forge worker run --once

# 2. 审核 / 编辑复盘
forge review-list              # 列 draft
forge review-diff <id>         # 看用户改了哪些字节
forge review-approve <id>
forge review-reject <id>

# 3. 知识管理
forge knowledge-list          # status=proposed 默认
forge knowledge-show <id>
forge knowledge-edit <id>      # 调 $EDITOR
forge knowledge-accept <id> \
    --rule-project demo \
    --rule-instruction "check tests first" \
    --rule-paths "src/**/*.py,tests/**/*.py"

# 4. 规则
forge rule-list [--status enabled|proposed|disabled]
forge rule-show <id>
forge rule-match --project demo --path src/sub/app.py --record
forge rule-stats <id>
forge rule-feedback <id> helpful|harmful|irrelevant|unknown

# 5. 检索 / 索引
forge scan                     # 重建 FTS5 + index.md
forge watch                    # mtime 轮询重建
forge search <query>
forge context --project demo [--path src/app.py]

# 6. 运维
forge doctor                  # 5 项只读诊断
forge metrics                 # §11 五项指标
forge session-info <id>       # JSON 调试
forge retention --days 30 --dry-run
forge retention --days 30
forge validate                # vault 自检

# 7. 历史回填
forge import-transcript <path> --project demo --session sess-1
```

## MCP server（可选）

```bash
python -m pip install -e ".[mcp]"
python -m context_forge.mcp_server
```

stdio transport；详情见 `docs/mcp-transport.md`。

## 数据契约

- Markdown 是事实源，SQLite 是可重建索引。
- SessionEvent 必须经过 Pydantic 校验。
- 事实型 claim 必须带 `evidence_ids`，否则 worker 拒收。
- 所有写入带 expected hash 冲突检测，hash 不匹配生成 `.conflict-<ts>` 副本。
- 凭证脱敏在 worker 调模型前完成，不写入 vault / 错误日志。

## 测试

```bash
python -m pytest tests/test_context_forge.py -v
```

40 条测试覆盖：幂等键、脱敏、worker 重放、knowledge accept → rule proposal
闭环、review-diff、metrics、rebuild history、hook e2e、MCP 5 工具、remote/local
provider MockTransport、session-info、rule-list/show。
