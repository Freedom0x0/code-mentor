# 执行计划: 优化 SKILL.md 新人友好度

## 执行顺序

### 阶段 1: 修改 SKILL.md（9 项改动）

1. **S1** 把 "When to Use" 节从末尾剪切，粘贴到 Overview 之后（第2节）
2. **S2** 在决策树 block 前加 `**（以下为中文速查决策树）**` heading
3. **S3a** "陪跑模式" 首次出现处加注释 `（mentor mode，陪跑模式）`
4. **S3b** "完成定义" 首次出现处加注释 `（definition of done，完成定义）`
5. **S4** `Rigor排查助手` → `严谨排查助手`（全局替换，共 2 处）
6. **S5** `§4 规则` → `（参见下方"收尾规则"部分）`
7. **M1** `superpowers:brainstorming` → `brainstorming`
8. **M2** Skill Collaboration 表末行加 `peaks-code` 条目
9. **M3** Test Cases 段 "subagent prompt" 后加说明句

### 阶段 2: 修改 README.md（1 项改动）

10. **M4** 修复 `evals/evals.json` 坏引用

### 阶段 3: 测试评审

11. 对照修改后的 SKILL.md，逐条评审 TC1–TC13，输出评审报告

## 回滚

所有改动均在 git 仓库内，可随时 `git diff HEAD` 查看，`git checkout .` 回滚。

## 验证命令

```bash
git diff HEAD -- SKILL.md README.md
```
