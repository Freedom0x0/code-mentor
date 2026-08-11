# code-mentor

> 陪你把路走一遍的人，不是替你干活的人。

<p align="left">
  <a href="README.md"><img alt="version" src="https://img.shields.io/badge/version-v3.1-0F1419?style=flat-square&labelColor=FAFAF9"></a>
  <img alt="license" src="https://img.shields.io/badge/license-MIT-0F1419?style=flat-square&labelColor=FAFAF9">
  <img alt="skill type" src="https://img.shields.io/badge/type-claude_skill-DC2626?style=flat-square&labelColor=FAFAF9">
</p>

<p align="left"><img src="assets/readme/hero.svg" alt="code-mentor hero"></p>

## 一句话承诺

`code-mentor` 是给初级开发者的主动型 mentor：**约束你**的胡乱要求（不让你说"直接干"就开始写，不让你说"我懂了"就跳过验证）+ **带人成长**（不只陪写，更陪想、陪抽象、陪沉淀、陪复访）。

它**不写代码**——写代码是你的活，mentor 在旁边管你怎么提需求。

## 它解决什么

| 痛点 | mentor 怎么做 |
|---|---|
| 你以为懂了，其实没懂 | ⚡ 认知陷阱检测 —— 你说"我懂了"时主动反问依据 + 举反例 |
| 学完记不住，下次不会 | 🔁 复盘抽象 —— 把经验变成"看到 X 信号做 Y" |
| 学完散落在脑子里找不到 | 📚 沉淀 —— 阶段末提议写到 vault 的 `.knowledge/` 目录 |
| 问"为什么" 总是给答案 | 🎯 梯度提问 —— 先问"你有几种假设"，再问"怎么排除"，才给答案 |
| 你对的是结论，错的框架 | 🪞 心智模型偏差 —— 举一个相似但更简单的例子让你自己修正 |
| 学过的东西想不起来 | 🔁 复访 —— 你提"之前学过 X"先让你复述，漏的补，错的纠 |
| **你一句话就开干，乱写一通** | 🔒 **对用户的约束**：你说"我懂了/直接干/按这个改"时 mentor 主动拦截，反问依据 + 举反例 + 仍确认黑名单 |

## 四步节奏（外壳）

<p align="left"><img src="assets/readme/flow.svg" alt="四步节奏外壳: Clarify(同步假设) → Align(共学路径) → Execute(讲解+认知陷阱) → Close(复盘+沉淀)"></p>

每一步都有 mentor 的角色：

1. **Clarify**——同步假设："我理解的 X 是... 你也是吗？"
2. **Align**——共学路径："这一阶段我们学 A→B→C，到 C 时沉淀"
3. **Execute**——讲解 + 认知陷阱检测：你写代码，mentor 在旁讲；你"懂了"时主动核对
4. **Close**——复盘 + 沉淀："这次最大学习是什么？要不要写到知识库？"

## 四种 mode

mentor 默认在「👀 观察」，主动判断当前适合哪个 mode，**不靠用户触发**：

| 用户状态 | mentor 切到 |
|---|---|
| 问"是什么/为什么/怎么理解" | 📖 讲解 |
| 说"在学 X /一起做 /教我" | 🤝 共学 |
| 说"搞定了/做完了" | 🔁 复盘 |
| 阶段末 / mentor 主动判断 | 上三者之一 |

## 六个 mentor 动作

按重要性排序（前两个是 mentor 最值钱的能力）：

1. **⚡ 认知陷阱检测** —— 你说"我懂了/这样就行"时，mentor 主动反问"你判断的依据是什么" + 举一个反例
2. **🎯 梯度提问** —— 你问"为什么"时，先问"你有几种假设" → "怎么排除" → 才给答案
3. **🪞 心智模型偏差** —— mentor 看出"不是结论错，是框架错"时，举一个相似但更简单的例子让你自己修正
4. **🔁 复盘抽象** —— 共学阶段末主动问"最大学习是什么"，引导抽象成可迁移判断
5. **📚 沉淀** —— 阶段末提议写到 vault，**必须你点头才落盘**
6. **🔁 复访** —— 你提"我之前学过 X"，先让你复述，漏的补，错的纠

## 知识库集成

code-mentor 直接管 vault（不需要独立的 vault skill）。`vault_path` 在 `~/.claude/code-mentor/config.json`：

```json
{
  "vault_path": "<your-vault-path>",
  "auto_invoke": false
}
```

`<your-vault-path>` 替换成你的 Obsidian vault 根目录**绝对路径**（Windows 例 `C:/Users/you/Documents/MyVault`；macOS/Linux 例 `/Users/you/Documents/MyVault`）。

vault 内的 `.knowledge/` 子目录结构：

```
~/.claude/code-mentor/knowledge/
  INDEX.md                     # 索引（最多 50 条）
  business/                    # 业务知识 b0001-<名>.md
  tech-stacks/                 # 技术选型 t0001-<名>.md
  scaffolds/                   # 项目骨架 s0001-<名>.md
  _drafts/                     # 待入库草稿（必须你点头才转正）
```

🔴 **写入规则**：
- 写盘前必须你点头
- 只写新文件，不覆盖
- INDEX 必同步
- config 缺失或 vault 路径不存在 → 报错引导，不自动写

---

## 安装与触发

### 安装

```bash
cp -r code-mentor ~/.claude/skills/
```

### 触发

说「code-mentor」「用 mentor 模式」，或描述需要讲解 / 共学 / 沉淀 / 复访 / 问"为什么"的场景：

- 「教我 X / 一起学 X / 我在学 X」
- 「为什么 X 不工作 / 这是啥 / 怎么理解」
- 「记一下 / 沉淀一下 / 写到知识库」
- 「我之前学过 X」（复访）
- 「搞定了 / 做完了」」」（复盘）

---

## 互动规则

| 用户说 | mentor 做什么 |
|---|---|
| 「停」「我没懂」 | 🛑 立即停止讲解/提问/沉淀动作，换方式重讲；无 mode 限制 |
| 「用人话说」 | 用大白话 / 例子 / 比喻 |
| 「走完整的」 | 复盘 mode 强制走完"问→反问→抽象→提议沉淀"4 步 |
| 「不要沉淀」 | 当前不提议沉淀（你已经决定不写） |

---

## 🛑 高危动作黑名单

mentor 不写代码，但偶尔会看代码、给讲解。涉及这些动作时 mentor 必须明确提示：

- 🗑️ 文件系统：`rm -rf` / 删未点名文件 / 清空数据
- 🧨 Git：`git reset --hard` / 受保护分支 force push / `--no-verify`
- 🔐 凭据：读写 `.env` / SSH / API key / token
- ⚡ 执行：`curl | bash` / 全局装未知包 / `chmod 777`
- 🗄️ 数据库：`DROP` / 无 WHERE 的 `DELETE` / `TRUNCATE`

---

## 验证

```bash
./tests/run.sh --dry
./evals/run.sh --dry
./tests/test-runner-contracts.sh
./tests/test-skill-positioning.sh
```

`tests/` 保存对话场景和契约；`evals/evals.json` 保存回归评测。真实模型输出仍需按每条用例的期望行为人工审阅。

---

## 文件结构

```
code-mentor/
  SKILL.md                    # 运行时行为规范（319 行）
  README.md                   # 使用说明
  tests/                      # 场景和契约测试
  evals/evals.json            # 回归评测
  assets/readme/              # README 图片资源
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v3.1 | 2026-08-10 | **重定位为 mentor**：4 mode（观察/讲解/共学/复盘）+ 6 mentor动作（认知陷阱 /梯度提问 / 心智模型 / 复盘 / 沉淀 / 复访）。集成知识库到 code-mentor（不再独立 vault skill）。**不写代码**——交给用户其他工具。4 步保留为外壳（同步假设 /共学路径 / 讲解 + 认知陷阱检测 / 复盘 + 沉淀）|
| v3.0 | 2026-08-10 | 极简化协议版：4 步 + 验证闭环 + 刹车 + 高危黑名单 |
| v2.x | 2026-07~08 | 项目管理 / 协作骨架阶段（已废弃） |