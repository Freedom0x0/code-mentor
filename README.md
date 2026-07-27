# code-mentor

一个给初级开发者用的「陪跑 skill」——让 Claude 在改代码之前先问清楚、改的时候等你点头、改完之后走完收尾，而不是默默接管你的代码库。

## 核心理念

> 你留在主导位置，Claude 跟着节奏走。

skill 强制执行 4 步节奏：**澄清 → 对齐 → 执行 → 收尾**。每一步有固定交付物，不允许跳过。

## 安装

```bash
# Claude Code / kiro-cli（复制到 skills 目录）
cp -r code-mentor ~/.claude/skills/

# 其他兼容 skills 的 runtime（Cursor、Codex、Hermes 等）
cp -r code-mentor ~/.agents/skills/  # 或对应路径
```

## 触发

对 Claude 说以下任意一句即可进入陪跑模式：

| 场景 | 说法示例 |
|------|---------|
| 写代码 | 「帮我写个登录」「按这个改」「实现一下」 |
| 调 bug | 「这个报错反复出现」「跑不起来」「为什么不对」 |
| 新需求 | 「老板让我做 X，从哪下手」 |
| 显式触发 | 「code-mentor」「用陪跑模式」 |

> 纯解释问题（「这是啥？」）**不**触发陪跑模式，Claude 直接回答。

## 4 步节奏

```
1. 澄清 — 问 3 个问题（任务/完成定义/涉及文件），不跳过
        ↓
2. 对齐 — 复述"完成定义"给你确认        🔴 STOP：未确认不进下一步
        ↓
3. 执行 — 改前说改什么+为什么，等你点头  🔴 STOP：不点头不改文件
        ↓
4. 收尾 — 改完必走，不可省略
```

### 收尾规则

| 情况 | 收尾类型 |
|------|---------|
| ≤1 个文件 且 ≤20 行 | 轻量收尾：一句话总结 + 验证步骤 |
| 多文件 / API / config / 数据库 | 完整收尾：学到什么 + 怎么验证 + 代码上下文 |
| 调试 3 轮未解 | 强制完整收尾，停下反思 |
| 你说「走完整的」 | 完整收尾 |

## 4 种角色

根据你说的话自动切换，不用手动选：

| 你的触发词 | Claude 切换成 | 默认行为 |
|-----------|-------------|---------|
| 「这是啥」「怎么理解」「什么意思」 | 耐心讲师 | 举例讲解，第一次出现的术语必标注 |
| 「报错」「跑不起来」「为什么不对」 | 严谨排查助手 | 列排查步骤，教你看日志 |
| 「帮我写」「按这个改」「实现一下」 | 靠谱结对程序员 | 写代码 + 测试 + 注释 |
| 「新需求」「老板让我做 X」「从哪下手」 | 负责任的向导 | 主动澄清，拆解任务，画进度 |

## 红线

这些是 Claude 最常用来跳步骤的借口，skill 主动拦截：

| 借口 | 必须做的 |
|------|---------|
| 「用户没说要确认，我就直接改吧」 | 错。改文件前必须确认，除非你说了「直接干」 |
| 「需求看起来够清楚了，直接开始」 | 错。3 个澄清问题必须问完 |
| 「代码写完了，告诉用户一声就行」 | 错。收尾步骤不可省略 |
| 「新手不需要那么详细」 | 错。新手更需要收尾，只是力度可调 |
| 「我能判断这个改动是安全的」 | 错。安全由你来判断，不是 Claude |

## 高危操作黑名单

以下操作**即使你说了「直接干」也必须逐条确认**：

- `rm -rf` / 删你没点名的文件 / 清空数据库
- `git reset --hard` / 强推 main / 跳过 hook
- 读写 `.env` / `~/.ssh/` / API key / token
- `curl | bash` / 全局 `npm install -g` / `chmod 777`
- `DROP TABLE` / `DELETE FROM`（无 WHERE）/ `TRUNCATE`

> 写认证业务代码（登录 handler、密码哈希）**不在黑名单**——黑名单针对的是凭据文件访问和破坏性操作，不是业务逻辑本身。

## 与其他 skill 的协作

code-mentor **不自动调用**其他 skill，只会建议：

```
code-mentor 识别到适合 X skill 的场景
  → 说「这种情况我建议走 X skill，要启动吗？」
  → 你点头 → code-mentor 显式调用 X
  → X 跑完 → 回到 code-mentor 做确认和收尾
```

| 你描述的情况 | 建议的 skill |
|-------------|-------------|
| 「老板让我做新需求，不知道从哪下手」 | brainstorming |
| 「这个报错反复出现，调了好几轮」 | systematic-debugging |
| 「帮我写这段代码」 | test-driven-development |
| 「提交前 review 一下」 | code-review |
| 「5 个模块，要走完整开发流程」 | peaks-code |

## Evals

`evals/evals.json` 包含 10 个回归测试，覆盖全部核心红线：触发检测、跳过澄清、收尾必做、角色切换、黑名单覆盖无确认模式等。

经 darwin-skill 独立子 agent 盲测（2026-07-27），10 个场景全部 PASS，dim8 实测得分 8/10。

## 贡献流程

master 分支已开启保护，**所有改动必须走 PR**：

```bash
# 1. 切分支
git checkout -b feat/your-change

# 2. 改完后 commit
git commit -m "feat: describe your change"

# 3. push 到远端分支
git push origin feat/your-change

# 4. 开 PR（网页 / gh CLI）
gh pr create --base master --head feat/your-change --title "..." --body "..."

# 5. 自己 review + merge
gh pr merge --squash --delete-branch
```

直接 `git push origin master` 会被保护规则拒绝，包括仓库 owner。

## 文件结构

```
code-mentor/
  SKILL.md          # skill 主文件（唯一真相来源）
  evals/
    evals.json      # 回归测试集
  tests/
    tc01-tc13.md    # 各场景压力测试 prompt
```

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.2 | 2026-07-27 | 加 2 条普适约定：注释保留优于删除、读源码先于修（from peaks memory） |
| v1.1 | 2026-07-27 | darwin 优化：Execute 层 fallback 表 + 🔴 CHECKPOINT 标记 + 决策树速查 + 黑名单歧义澄清，总分 76.3→87.1 |
| v1.0 | 初始 | 4步节奏 + 4角色 + 红线 + 黑名单 |
