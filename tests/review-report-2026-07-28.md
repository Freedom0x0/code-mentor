# 测试评审报告 — code-mentor v1.2+

**评审日期**: 2026-07-28  
**评审范围**: TC1–TC13，对照修改后的 SKILL.md（S1–M3 已应用）  
**评审方法**: Explore agent 独立阅读 SKILL.md + 全部测试文件，逐条比对

---

## 评审结论汇总

| TC  | 结论     | 核心问题 |
|-----|----------|---------|
| TC1 | **PARTIAL** | "up to three questions" 与 Red Lines "all 3 must be asked" 互相矛盾 |
| TC2 | **PARTIAL** | no-confirmation 模式下未明确保留单句声明；模式切换无需确认回执规定 |
| TC3 | **PARTIAL** | 收尾后缺少「下一步做什么？」指令；"继续" 触发收尾的规则未显式写出 |
| TC4 | **PASS**    | 覆盖良好；"具体例子"隐含于解释风格，风险极低 |
| TC5 | **PASS**    | Execute 歧义规则 + 决策树双重覆盖 |
| TC6 | **FAIL**    | 整个工作流中无"用户显式触发 mentor mode 但任务非开发"的分支 |
| TC7 | **PARTIAL** | skill 命名空间（`superpowers:`）与 SKILL.md 中裸名 `brainstorming` 不一致 |
| TC8 | **PARTIAL** | 假设原因数量（"2–3 条"）未规定；同 TC7 的命名空间问题 |
| TC9 | **PARTIAL** | 无指代对象的"这是啥？"时 Claude 应如何回应未规定 |
| TC10 | **PASS**   | ≤1 文件 / ≤20 行 → 轻量收尾规则明确；"下一步"不在 failure signals 中 |
| TC11 | **PARTIAL** | 接口/上下文节有"（if applicable）"限定语，测试要求强制但 SKILL.md 可选 |
| TC12 | **FAIL**    | 无"peaks-code 已运行时 code-mentor 应退让"的指令；"切到 peaks" 只在 TC 表里 |
| TC13 | **PARTIAL** | 缺少"范围过大时不强行用 mentor mode 接收任务"的明确禁止规则 |

**统计：PASS 3 / PARTIAL 7 / FAIL 2**

---

## 逐条详情

### TC1 — 触发 + 澄清
**PARTIAL**

✅ 覆盖的：When to Use 触发条件、3 个澄清问题内容、Red Lines"不猜不改"规则  
⚠️ 缺口：`§1. Clarify` 写的是 "ask **up to** three questions"（最多 3 个），而 Red Lines 表写的是 "all 3 clarifying questions must be asked"——两处直接矛盾。Claude 可能以"最多 3 个"为准，只问 1–2 个。  
⚠️ 缺口：SKILL.md 未说明"先问模式意愿，再问 3 个澄清问题"的先后顺序，顺序可能被 Claude 颠倒。

**建议修复**：`§1. Clarify` 的 "up to three" 改为 "all three of the following"。

---

### TC2 — 跳过确认（直接干模式）
**PARTIAL**

✅ 覆盖的：no-confirmation 模式触发词（"直接干" / "别问了"）、收尾必做、模式全 session 持续  
⚠️ 缺口：Execute 节将"声明改动"和"等待点头"绑定在一起。no-confirmation 模式移除"等待点头"，但未明确保留"声明"。TC2 要求改前仍需一句话声明。  
⚠️ 缺口：SKILL.md 没有要求 Claude 显式说"我现在进入直接干模式"作为模式切换回执。

**建议修复**：Execute 节补一句："no-confirmation 模式仍需在改动前用一句话说明改了什么；移除的只是等待确认"。

---

### TC3 — 继续之前先走收尾
**PARTIAL**

✅ 覆盖的：收尾必做（Red Lines）、轻/完整收尾判断规则  
⚠️ 缺口：SKILL.md 的收尾节末尾无"收尾后问'下一步做什么？'"指令。TC3 把这条列为必须行为。  
⚠️ 缺口：SKILL.md 没有说"用户说'继续'时先做收尾再继续"——只说改完之后要收尾，没说用户主动要求继续时 Claude 应当拦截并先收尾。

**建议修复**：`§4. Close` 末尾加"完成收尾后以'下一步做什么？'结束，等待用户指示"。

---

### TC4 — 耐心讲师角色
**PASS**

✅ 覆盖良好：角色触发词、"举例讲解"解释风格、术语首次注释规则、读写操作不触发收尾。  
ℹ️ 微小风险："给出具体例子"隐含于角色描述，非强制要求；实际失败概率低。

---

### TC5 — 模糊需求追问
**PASS**

✅ 全面覆盖：Execute 节歧义处理 + 决策树"需求模糊 → 问 2-3 个澄清问题"双重保障。

---

### TC6 — 错误上下文（邮件任务）
**FAIL**

✅ 覆盖的：When to Use 说明了触发场景是开发任务  
❌ 缺口（关键）：整个工作流（Clarify/Align/Execute/Close/Roles/决策树）均无"用户已显式说'用陪跑模式'但任务非开发"的分支。仅 TC 汇总表里有一句描述，但那是测试文档，不是 Claude 的行为指令。  
→ Claude 收到"用陪跑模式帮我写邮件"后，会正常进入 4 步工作流，直接开始"澄清"邮件需求。

**建议修复**：在 `§1. Clarify` 或决策树加一条分支："若用户显式触发 mentor mode 但任务明显非开发场景（如写邮件），礼貌提示范围不匹配，询问是否切回普通模式，等待用户决定后再继续。"

---

### TC7 — 建议 brainstorming skill
**PARTIAL**

✅ 覆盖的：Responsible guide 角色切换、协作流程"先建议后等点头"、禁止自动调用  
⚠️ 缺口：SKILL.md 协作表中写的是 `brainstorming`（无前缀），TC7 测试文件要求 Claude 说 `superpowers:brainstorming`。若 Claude 按 SKILL.md 裸名建议，会与测试预期不一致。

**建议修复**：与 TC8 一并确认 skill 命名空间约定（测试改名或 SKILL.md 加命名空间），保持一致。

---

### TC8 — 调试角色 + 建议 systematic-debugging
**PARTIAL**

✅ 覆盖的：严谨排查助手角色切换（v1.2+ 已统一名称）、Step 0 读源码、协作表触发、禁止自动调用  
⚠️ 缺口：TC8 要求"假设 2–3 个可能原因"，SKILL.md 只说"假设原因"，没有数量下限。Claude 可能只给 1 个假设。  
⚠️ 缺口：同 TC7 的 `superpowers:` 命名空间问题。

**建议修复**：角色描述中在"假设原因"后加"（至少 2 个）"。

---

### TC9 — 纯问题不触发 mentor 模式
**PARTIAL**

✅ 覆盖的：When to Use "纯解释问题不触发"、决策树顶层分支  
⚠️ 微小缺口："这是啥？"完全没有指代对象时 Claude 应如何回应（是问用户"你指的是什么"还是给出通用解释）—— SKILL.md 未规定。  
→ 不影响 TC9 的核心验证（不触发 mentor mode），但用户体验可能不一致。

---

### TC10 — 轻量收尾（小改动）
**PASS**

✅ 全面覆盖：≤1 文件 / ≤20 行 → 轻量收尾规则明确，一句话总结 + 验证步骤均有规定。  
ℹ️ 注意：TC10 也要求"收尾后问'下一步做什么？'"，但该项不在 TC10 的 failure signals 里，属于低风险缺口。

---

### TC11 — 完整收尾（多文件 + API）
**PARTIAL**

✅ 覆盖的：多文件 / API → 完整收尾触发条件、3 个收尾内容（学到什么、如何验证、代码上下文）  
⚠️ 缺口：接口/上下文节注有 "(if applicable)"，使该节成为可选项。TC11 要求多文件 API 场景下必须输出，但 Claude 可合理解读为"此处不适用"而跳过。

**建议修复**：在收尾规则补充说明"多文件 / API 改动时，接口/上下文节为必选项"。

---

### TC12 — 与 peaks-code 共存
**FAIL**

✅ 覆盖的：peaks-loop 共存机制说明（描述性）、禁止自动调用任何 skill 的 Hard Limit  
❌ 缺口 1：Peaks-Loop 章节是描述性文字（"no priority or suppression mechanism"），无任何"peaks-code 已运行时 code-mentor 应退让"的可执行指令。决策树和工作流节均无此分支。  
❌ 缺口 2："切到 peaks"的处理（建议切换、不自动调用、不静默切换）只出现在 TC 汇总表，工作流节无对应指令。  
→ 两个子场景均没有可执行的行为规则支撑。

**建议修复**：  
1. 在决策树或 Roles 节加分支："若用户发出'切到 peaks / 用 peaks-code'信号，建议切换，不自动调用，等待确认"。  
2. 在 Peaks-Loop 节加指令："若 peaks-code 已在编排中（用户通过 /peaks-code 进入），code-mentor 不接管；在该 pipeline 中作为普通 Claude 辅助即可"。

---

### TC13 — 建议 peaks-code 处理大范围需求
**PARTIAL**

✅ 覆盖的：协作表 "peaks-code" 条目（v1.2+ 已补充）、协作流程"先建议后等点头"、Hard Limit 禁止自动调用  
⚠️ 缺口：SKILL.md 无显式规则"当建议 peaks-code 后不得将该任务纳入 mentor mode 继续处理"。Claude 可能建议 peaks-code 后同时开始 mentor mode 澄清。

**建议修复**：在协作流程说明中加"若任务超出 mentor mode 范围，建议对应 skill 后停止 mentor mode 接收该任务，等待用户决定"。

---

## 横切问题（多个 TC 共同影响）

### 问题 A：`§1. Clarify` 与 Red Lines 的矛盾
- "up to three" vs "all 3 must be asked"
- 影响：TC1

### 问题 B：收尾后缺少转换提示
- "下一步做什么？" 在 TC3/TC10/TC11 中均被测试，但 SKILL.md 无此规定
- 影响：TC3、TC10（低风险）、TC11（低风险）

### 问题 C：No-confirmation 模式声明保留
- 声明 + 等待被绑定，模式取消"等待"时是否保留"声明"未明确
- 影响：TC2

### 问题 D：Skill 命名空间不一致
- SKILL.md 用裸名，测试文件用 `superpowers:` 前缀
- 影响：TC7、TC8
- **建议**：统一测试文件为裸名（因 SKILL.md 是权威），或在 SKILL.md 明确写出前缀

### 问题 E：两个 FAIL 需要额外 SKILL.md 规则
- TC6：需加"非开发任务的 mentor mode 请求"处理分支
- TC12：需将 peaks 共存逻辑从描述性改为可执行指令

---

## 建议修复优先级

| 优先级 | 修复项 | 影响 TC |
|--------|--------|---------|
| 🔴 必须 | TC6 处理分支（非开发任务 + 已触发 mentor mode） | TC6 FAIL |
| 🔴 必须 | TC12 peaks-code 行为指令（退让 + "切到 peaks"处理） | TC12 FAIL |
| 🟡 应该 | "up to three" → "all three"（消除矛盾） | TC1 |
| 🟡 应该 | 收尾后加"下一步做什么？"指令 | TC3 |
| 🟡 应该 | no-confirmation 模式保留声明 + 模式切换回执 | TC2 |
| 🟡 应该 | 完整收尾接口/上下文节：多文件 API 时改为必选 | TC11 |
| 🟢 建议 | 角色描述"假设原因（至少 2 个）" | TC8 |
| 🟢 建议 | 统一 skill 命名空间 | TC7、TC8 |
| 🟢 建议 | TC13 加"范围超出时停止 mentor mode 接收" | TC13 |
