# PRD: 修复 SKILL.md 行为缺口（来自测试评审报告）

## 背景

前一任务（07-28-skill-newbie-optimization）的测试评审发现：
- 2 个 FAIL（TC6、TC12）：SKILL.md 完全缺少对应的可执行分支
- 7 个 PARTIAL：规则不明确或存在矛盾，导致 Claude 可能走偏

本任务按评审报告的优先级逐项修复。

## 修复清单

### 🔴 必须修复（FAIL → PASS）

**F1 — TC6：非开发任务进入 mentor mode 的处理分支**
- 当前：SKILL.md 只说"纯解释问题不触发"，缺少"用户已显式触发但任务非开发"分支
- 要修复：在决策树 + §1. Clarify 加分支规则："若用户说'code-mentor'/'用陪跑模式'但任务明显非开发（写邮件等），礼貌提示范围不匹配，询问是否切回普通模式，等用户决定"

**F2 — TC12：peaks-code 共存的可执行指令**
- 当前：Peaks-Loop 章节是纯描述性，无任何行为指令
- 要修复（两条）：
  - 若 peaks-code 已在编排中，code-mentor 不接管，作为普通 Claude 辅助
  - 若用户在 mentor mode 说"切到 peaks"，建议切换到 peaks-code，不自动调用，等待确认

### 🟡 应该修复（PARTIAL → PASS）

**P1 — TC1："up to three" 与 Red Lines "all 3" 矛盾**
- §1. Clarify 的 "ask up to three questions" 改为 "ask all three of the following questions"

**P2 — TC3/TC10/TC11：收尾后转换提示缺失**
- §4. Close 末尾加："完成收尾后，以'下一步做什么？'结束，等待用户指示"

**P3 — TC2：no-confirmation 模式保留声明 + 模式切换回执**
- Execute 节补："no-confirmation 模式仍需在改动前用一句话说明改了什么；移除的只是等待确认"
- 同处补："切换到 no-confirmation 模式时，需用一句话回执（如'好，直接干，我会声明每次改了什么但不再等你点头'）"

**P4 — TC11：完整收尾接口/上下文节由可选改为必选（多文件/API 时）**
- Close 规则中，"Interface / context (if applicable)" 的 "(if applicable)" 注改为显式说明：多文件 / API 改动时为必选项

**P5 — TC7/TC8：skill 命名空间统一**
- 测试文件 tc07 / tc08 中的 `superpowers:brainstorming` / `superpowers:systematic-debugging` 改为裸名（以 SKILL.md 为权威）

### 🟢 建议修复（锦上添花）

**O1 — TC8：假设原因数量下限**
- 严谨排查助手角色描述加"（至少列出 2 个假设原因）"

**O2 — TC13：建议 peaks-code 后停止 mentor mode 接收该任务**
- 协作流程说明加："若建议对应 skill 后任务超出 mentor mode 范围，停止接收该任务，等待用户决定"

## 验收标准

- [ ] TC6 所有 checklist 项在 SKILL.md 中有明确可执行规则支撑
- [ ] TC12 两个子场景在 SKILL.md 中有明确可执行规则支撑
- [ ] §1. Clarify 中只有"ask all three"，无"up to"表述
- [ ] §4. Close 末尾有转换提示指令
- [ ] Execute 节说明 no-confirmation 模式保留声明 + 有切换回执规定
- [ ] 完整收尾接口/上下文节注明多文件/API 时必选
- [ ] tc07.md + tc08.md 中 superpowers: 前缀已去除
- [ ] 评审报告中所有 🔴/🟡 条目不再有对应缺口
