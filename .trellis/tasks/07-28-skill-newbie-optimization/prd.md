# PRD: 优化 SKILL.md 新人友好度 + 测试评审

## 背景

`SKILL.md` 是 code-mentor skill 的唯一真相来源（single source of truth），
Claude 加载它来决定陪跑行为。README.md 是面向真实用户的文档。
当前版本（v1.2）经过数轮迭代，但存在一系列**新人可用性**问题，
导致第一次使用的初级开发者难以正确触发和使用 skill。

## 目标

1. **优化 SKILL.md**：消除阻碍新人理解和使用的问题，不改变核心行为逻辑
2. **评审 13 个测试用例**：对照 SKILL.md 逐条评估，给出 PASS/FAIL + 说明
3. **同步修正 README.md**：修复已知的坏引用（`evals/evals.json` 不存在）

---

## 问题清单（严重影响新人首次使用）

| # | 问题 | 位置 |
|---|------|------|
| S1 | "When to Use" 放在最后（line 272），新人必须读完全文才知道怎么触发 | SKILL.md:272 |
| S2 | 决策树（line 32-46）整段中文内嵌于英文文档，无语言切换提示 | SKILL.md:32-46 |
| S3 | "陪跑模式"、"完成定义" 在未解释前直接使用 | SKILL.md:39,60 |
| S4 | 角色名 `Rigor排查助手`（中英混搭）与 README 的 `严谨排查助手` 不一致 | SKILL.md:110 |
| S5 | `§4 规则` 是死引用（文档用命名标题，无 §N 编号） | SKILL.md:76 |
| M1 | `superpowers:brainstorming` 与表格 `brainstorming` 格式不一致 | SKILL.md:175,195 |
| M2 | Skill Collaboration 表缺 `peaks-code` 条目（README 有，SKILL.md 无） | SKILL.md:195-198 |
| M3 | Test Cases 中 "subagent prompt" 未说明如何运行 | SKILL.md:231 |
| M4 | README 中 `evals/evals.json` 引用不存在的文件 | README.md:111,140-147 |

---

## 不在本次范围内

- 修改核心 4 步行为逻辑
- 改写/增删 tc01-tc13.md 内容
- 创建 evals.json（评测结果已在 README 文字描述中）

---

## 验收标准

- [ ] SKILL.md: "When to Use" 提前到第 2 节
- [ ] SKILL.md: 决策树添加明确的中文语言标注 heading，消除突然切换感
- [ ] SKILL.md: "陪跑模式" 和 "完成定义" 首次出现时加括号英文注释
- [ ] SKILL.md: 角色名 `Rigor排查助手` → `严谨排查助手`（与 README 一致）
- [ ] SKILL.md: `§4 规则` → 改为明确 section 引用
- [ ] SKILL.md: `superpowers:brainstorming` → `brainstorming` 统一
- [ ] SKILL.md: Skill Collaboration 表补充 `peaks-code` 条目
- [ ] SKILL.md: Test Cases 的 "subagent prompt" 加一句说明
- [ ] README.md: `evals/evals.json` 坏引用修复
- [ ] 输出 TC1–TC13 测试评审报告（PASS/FAIL + 理由）
