# Context Forge 技术方案自审

日期：2026-09-15

评审对象：[technical-design-context-forge.md](../technical-design-context-forge.md)

结论：**方向可行，方案暂不具备直接实现条件。** 需要先补齐数据契约、生命周期和安全边界，再开始编码。当前最危险的问题不是技术选型，而是系统在自动处理和人工编辑同时发生时，可能重复生成、覆盖用户内容，或让错误规则长期影响后续会话。

## P0：开始实现前必须解决

### 1. 状态机把不同对象混在了一起

主方案第 6 节把 `captured -> sanitized -> extracted -> draft -> approved -> compiled -> enabled -> verified` 写成一条链，但这些状态分别属于 Session、Job、Review、Knowledge 和 Rule。这样会导致实现者无法判断一次转换更新哪个对象，也无法表达“复盘被拒绝但会话已处理”“知识批准但规则尚未编译”等合法情况。

建议拆成独立状态机：

```text
Session: captured -> parsed -> redacted -> retained | discarded
Job: queued -> running -> succeeded | retryable | dead_letter
Review: draft -> approved | rejected | superseded
Knowledge: proposed -> accepted -> revised | conflicted | archived
Rule: proposed -> enabled -> verified | disabled | stale | archived
```

每个状态转换都应定义操作者、输入、输出和可重复执行行为。

### 2. 队列声称支持幂等，但表结构没有幂等键

第 16 节的 `jobs` 表没有 `idempotency_key`，第 16 节末尾却要求用它去重。SessionEnd 和 PreCompact 可能为同一会话投递多个任务；没有数据库唯一约束，worker 崩溃重试也可能生成多个草稿。

至少增加：

```sql
idempotency_key TEXT NOT NULL UNIQUE,
lease_expires_at TEXT,
```

并定义 key 规则，例如 `review:{session_id}:{transcript_hash}`。文件输出也必须使用临时文件、fsync、原子 rename 和目标 hash 检查。

### 3. 原始 transcript 的来源和生命周期没有定义

第 3、5、9 节同时要求本地保存 transcript、后台稍后读取 transcript、模型前脱敏，但没有规定 Claude Code 原始文件何时可能被删除、保存多久、谁可以读取、是否复制到 Context Forge 目录，以及 worker 读取失败时如何恢复。

必须明确：

- 默认只保存引用还是复制原文。
- 原文、脱敏副本和提取结果各自的 retention policy。
- `local_only` 是否允许本地模型，还是只意味着跳过自动提取。
- 原始 transcript 的文件权限和日志脱敏规则。
- 用户如何删除一个 session 的全部派生数据。

## P1：MVP 前必须明确

### 4. Obsidian 外部编辑同步不完整

方案把 Markdown 定义为事实源，但只设计了程序的 `update(expected_hash)` 和 `rebuild_index()`。没有定义用户在 Obsidian 中编辑、移动、删除或修改 frontmatter 后，系统如何发现和解释这些变化。

建议把文件同步定义为独立流程：

```text
scan/watch -> parse -> validate -> upsert index -> mark invalid/conflict
```

程序更新已有文件时使用 `expected_hash`；用户修改后不覆盖，重新解析为新版本。`index.md` 最好被标记为生成文件，避免它既是事实源又是人工编辑入口。

### 5. “通知用户审核”没有实现边界

第 5 节要求 worker 通知用户，但没有选择通知方式。CLI 轮询、系统通知、下一次 SessionStart 提示和 MCP 查询的用户体验不同，也影响 MVP 是否真的闭环。

MVP 应明确采用一种方式：例如 worker 只写 `pending_reviews`，下一次 `forge review list` 或 SessionStart 显示待审列表；系统通知放到后续版本。验收标准应包含“用户能发现草稿”，而不是只验证文件已经生成。

### 6. Review、Knowledge 和 Rule 的生成边界互相矛盾

第 6 节说 Knowledge 由一条或多条已确认复盘合并而成；第 14 节又让 `approve()` 直接返回 `KnowledgeItem`；第 11 节则要求确认后立即生成候选规则。这让“确认一次”到底批准复盘、知识还是规则变得含糊。

建议采用明确的两步：

```text
approve review -> create/update KnowledgeItem
accept rule proposal -> enable RuleCandidate
```

规则可以自动生成 proposal，但不能因为复盘批准就自动启用。

### 7. RuleFeedback 还不足以证明规则有效

当前反馈只有 `helpful|harmful|irrelevant`，无法区分规则被展示、被 AI 使用、被用户采纳和最终任务成功。单纯把测试通过归因给规则也会产生错误因果关系。

建议至少记录：

```text
presented -> acknowledged -> applied -> outcome
```

其中 outcome 需要允许 `unknown`。MVP 可以只做人工反馈，但数据模型要保留事件发生时间、规则版本、命中条件和 session_id。

### 8. “本地优先”与 Claude Agent SDK 的费用、账号和网络行为未闭合

第 10 节直接列出 Claude Agent SDK，却没有规定模型调用是使用 Claude Code 用户订阅、API key 还是本地模型，也没有失败时的降级策略。竞品对 SDK 订阅资格的说明不能替代本项目自己的运行契约。

MVP 应明确模型 provider 接口和配置：未配置 provider 时，仍能运行 capture、vault、索引和人工 review；只有用户显式配置模型后才启用自动提取。这样核心数据链路不会被网络、认证和费用阻断。

## P2：实现时应补齐

### 9. 领域接口仍然是示意代码

第 14 节的 Protocol 缺少错误类型、事务边界、分页、版本号、异步行为和返回的持久化 ID。`VaultRepository.update()` 只返回 `None`，无法表达冲突、验证失败和原子写入失败。

实现前应为每个接口写出输入 schema、错误枚举和最小测试。尤其要区分：用户拒绝、内容冲突、格式无效、暂时不可用和系统错误。

### 10. SQLite 并发和迁移策略没有写

虽然第一版只有单 worker，CLI、SessionEnd hook 和 worker 仍可能同时访问数据库。需要定义 WAL、busy timeout、事务隔离、任务 claim SQL、schema version 和迁移工具。`locked_at` 单独存在不足以防止两个进程同时领取任务。

### 11. 安全策略缺少路径与输出约束

“不读取敏感文件”不能覆盖 transcript 已经包含秘密的情况，也不能防止 vault 路径、符号链接和文件名造成越界写入。需要规定 vault 根目录 canonicalization、拒绝越界路径、符号链接策略、文件权限，以及错误日志和模型请求体不能回显原文。

### 12. 规则 scope 还不够表达真实适用条件

当前 scope 只提到项目、路径、技术栈，但规则通常还依赖分支、语言、运行环境、版本和证据时间。MVP 可以只支持 project + path，但 schema 要允许扩展，并明确未知 scope 是否禁止启用。

## 保留的判断

以下方向经过审查仍然成立：

- Markdown 是用户可拥有的事实源，SQLite 是可重建索引。
- Hook 只投递任务，模型处理放到 worker。
- Review、Knowledge、Rule 分开建模。
- 第一版采用路径、关键词和 FTS5，暂不引入向量数据库。
- 规则必须带来源、作用域、命中解释和撤销能力。

## 建议的修订顺序

1. 拆分各领域对象的状态机和事件。
2. 补齐 Session、Evidence、Review、Knowledge、Rule、Feedback 的 JSON Schema。
3. 把幂等键、租约、重试和 dead-letter 写入 jobs 契约。
4. 定义 transcript retention、删除和 provider 配置策略。
5. 定义 Markdown watcher/scan、冲突和 index.md 生成规则。
6. 收窄 MVP：先完成 capture → review → approve → vault；规则启用和反馈作为第二个垂直切片。
7. 再开始实现 SQLite、vault 和 worker。

