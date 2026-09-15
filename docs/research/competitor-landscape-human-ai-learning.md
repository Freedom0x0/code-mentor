# 人机共学产品方向调研

日期：2026-09-15

## 结论

方向有价值，也具备工程可行性，但差异点不能停留在“给 AI 加记忆”。主流编程助手已经能自动记忆、加载规则和读取项目说明。更有机会的产品定义是：把开发会话中的证据整理成用户可审阅的复盘，再把被确认、经过验证的经验转成有作用域、有来源、可撤销的规则，同时保留一份人类可读的 Obsidian 知识资产。

## 竞品与相邻方案

| 方案 | 已解决的问题 | 暴露的空白 |
|---|---|---|
| Claude Code memory / `CLAUDE.md` | 自动记忆偏好和项目经验；规则可按项目、用户和路径组织；Markdown 可编辑 | 记忆是上下文提示，不是强制策略；启动只加载 `MEMORY.md` 前 200 行或 25KB；没有面向人类学习的结构化复盘流程 |
| Devin Desktop / Cascade Memories & Rules | 自动记忆与手写规则分离；支持 global、workspace、system 层级和 always-on、glob、manual 等激活方式 | 官方建议可靠知识写入 Rule 或 `AGENTS.md`；自动记忆本地化且不提交仓库；规则与知识的生命周期仍由用户维护 |
| Mem0 | 提供 user/session/agent 多层记忆、SDK、服务端和混合检索；官方 README 描述了实体链接、BM25、语义检索和时间推理 | 面向通用 AI 个性化，不负责开发复盘、Obsidian 资产、人类确认或代码规则验证 |
| Basic Memory | Markdown-first、本地文件、frontmatter、Obsidian wikilink；支持全文、语义、混合和图检索，并提供 schema/index 一致性工具 | 文档强调结构和索引校验，没有明确的事实正确性验证或自动规则提炼闭环 |
| claude-mem | 通过 Claude Code hooks 自动捕获工具和会话活动，生成摘要与持久观察，并提供 MCP 检索和渐进披露 | 更偏索引化记忆与会话历史；公开 README 没有清楚定义 Obsidian Markdown 作为事实源，也没有正式的人工确认规则对象 |
| Hindsight | 用 retain / recall / reflect 三种操作，把事实、经历、观察和 mental model 分层；观察保留精确证据与 proof count，支持时间、语义、关键词和实体关系检索，也可投影为 Markdown knowledge pages | 强大的通用 agent memory 基础设施，通常需要服务端、数据库和 LLM；它解决“代理学习”，但没有聚焦 Obsidian 复盘、用户学习体验和人工确认入库 |
| claude-memory-compiler | 通过 Claude Code 的 SessionEnd / PreCompact hooks 捕获 transcript，先写 daily log，再编译为 concepts、connections、Q&A；用 Markdown index 做检索，并提供 broken links、孤儿、矛盾和过期检查 | 已覆盖“会话 → 知识库 → 下次注入”的完整自动链路，但规则提炼、人工确认、规则效果反馈和项目级作用域仍可深化；它是社区项目，不是 Anthropic 官方产品 |
| code-mentor 当前实现 | 已有 Clarify → Align → Execute → Close 节奏；强调认知陷阱、复盘抽象、用户点头后写入 vault；已有 `_drafts`、INDEX 和知识分类 | 当前主要是 Claude skill；跨助手接入、会话 transcript 解析、知识检索、规则效果反馈仍需产品化 |

## 价值判断

价值分成两条闭环：

1. 对 AI：项目上下文、用户偏好和已验证的失败经验会减少重复澄清、错误修改和上下文丢失。
2. 对人：复盘把“这次怎么修好”提升为“看到什么信号时应做什么判断”，形成可搜索、可编辑、可迁移的个人知识库。

真正可衡量的价值不是生成了多少笔记，而是后续任务是否更快、更少返工，以及用户是否能解释和复用这条经验。应关注首次成功率、重复错误率、复盘确认率、规则命中后的修复率和错误规则撤销率。

## 可实现性

技术路径成立：在支持 hook 的助手中，SessionEnd 可取得 `session_id`、`cwd` 和 `transcript_path`。Claude 官方文档明确说明 SessionEnd 只能做清理，不能阻止退出；默认超时 1.5 秒，适合写入本地队列，不适合在退出时同步调用模型。后台 worker 或下一次 SessionStart 再解析 transcript，可以生成复盘草稿。

建议的流水线是：会话结束投递任务 → 脱敏和按项目归档 → 提取问题、尝试、证据、结果和可迁移判断 → 生成 Obsidian 草稿 → 用户确认 → 写入知识库 → 从确认内容生成候选规则 → 在后续任务中以小范围、可解释的方式检索 → 记录规则是否帮助或造成错误 → 允许修改、降权和撤销。

Hindsight 证明“经验、证据、观察、长期模型”可以在一个记忆系统中分层；`claude-memory-compiler` 证明只用 hooks、后台进程、daily Markdown、索引和 lint，就能实现个人规模的知识闭环。因此 MVP 不需要先引入向量数据库或复杂知识图谱。

## MVP 边界

先只做 Claude Code + Obsidian + 本地 Markdown：

- `SessionEnd` 只投递 transcript 路径，避免退出阻塞。
- 下一次启动或显式命令生成一份复盘草稿，不自动写正式知识。
- 用固定 schema 保存来源会话、项目、问题、证据、结论、适用范围和置信度。
- 用户确认后写入 `_drafts` 转正知识，并同步 INDEX。
- 规则先作为候选 Markdown，在下一次任务中展示“为什么命中、来自哪次复盘”，提供禁用和撤销。

跨编辑器适配、向量数据库、自动强制规则、团队共享和复杂知识图谱都放到验证 PMF 之后。

## 主要风险

- **幻觉沉淀**：模型可能把猜测写成经验。每条知识必须带 transcript 证据和“事实 / 推断 / 待验证”区分。
- **知识污染**：过时规则会持续误导 AI。需要作用域、版本、最后验证时间、成功/失败反馈和一键撤销。
- **隐私与凭据**：transcript 可能含 token、`.env` 内容和内部代码。解析前先做本地脱敏，默认不上传。
- **打扰成本**：每次会话都问复盘会让用户厌烦。仅在有明确结果、重复失败或高信息密度时提议，并允许批量处理。
- **Obsidian 生态碎片化**：Markdown 是好的最低共同点，但不要依赖特定插件；链接、frontmatter 和目录约定应可配置。

## 来源

- Claude Code, “How Claude remembers your project”: https://code.claude.com/docs/en/memory.md
- Claude Code, “Hooks reference”, SessionEnd: https://code.claude.com/docs/en/hooks.md
- Devin Desktop, “Memories & Rules”: https://docs.devin.ai/desktop/cascade/memories.md
- Mem0 official repository README: https://github.com/mem0ai/mem0
- Basic Memory README: https://github.com/basicmachines-co/basic-memory#readme
- Basic Memory documentation: https://docs.basicmemory.co/
- claude-mem README: https://github.com/thedotmack/claude-mem#readme
- claude-mem repository: https://github.com/thedotmack/claude-mem
- Hindsight README: https://github.com/vectorize-io/hindsight
- Hindsight documentation: https://hindsight.vectorize.io/
- claude-memory-compiler README: https://github.com/coleam00/claude-memory-compiler
- claude-memory-compiler technical reference: https://github.com/coleam00/claude-memory-compiler/blob/main/AGENTS.md
- 本仓库产品现状：[README.md](../../README.md)

注：claude-mem 的直接 raw README 在本环境不可用，因此相关判断限定在其公开 README 和仓库说明，不作穷尽性结论。
