# code-mentor 六条新约束 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 code-mentor 加 6 条约束，让它在众多 skill 之上补齐新手缺口 —— 输入先核实、输出说人话、影响面先摆清。

**Architecture:** 纯 Markdown 规则文件编辑。改 3 个文件：`SKILL.md`（6 个落点）、`tests/CASES.md`（新增 TC36–47）、`evals/evals.json`（新增 id 25–36）。每条约束一个 Task，各自带自己的测试用例一起提交，互不依赖。最后一个 Task 同步主流程图并做全文一致性检查。

**Tech Stack:** Markdown、JSON。无构建、无测试运行器 —— 验证靠 `grep` 断言关键约束文本存在，靠 `python -m json.tool` 断言 JSON 合法。

## Global Constraints

以下为全局约束，每个 Task 的要求都隐含包含本节：

- 🔴 **code-mentor 不改任何其他 skill 的步骤或顺序，只对"交到用户面前的东西"加一道过筛。**
- 🔴 **brainstorming 的推荐顺序以 brainstorming 为准** —— 不得新增"推荐标签延后""不许标推荐""不许排第一"之类的要求。
- 🔴 **取舍标准**：老手自己能做到的不加；只加新手做不到、且做不到就会出事的。
- 🔴 **Mentor 基调**：不只挡事，还要带人。指出问题后补一句"下次你自己可以怎么判断"。
- 🔴 **所有面向用户的示例文本必须写后果，不写术语。** 反例 `order.js:88 调用处参数不匹配`；正例 `order.js:88 也在调它，不一起改下单会直接报错`。
- 🔴 **不点名任何具体 skill 名来做约束**（委派契约必须是通用形态）。skill 触发是 harness 级的，穷举必输。
- 文件全部为中文内容，保持现有 SKILL.md 的排版风格：`🔴` 标最高优先级、表格优先于长段落、示例用 `>` 引用块。
- 每个 Task 独立 commit，commit message 用中文 + 语义化前缀。
- 编辑 `SKILL.md` 一律用精确字符串替换，不整文件重写。
- 本仓库 `git config core.autocrlf` 会把 LF 转 CRLF，`git add` 时出现 `LF will be replaced by CRLF` 警告属正常，不是错误。

**参考规格：** `docs/superpowers/specs/2026-08-03-mentor-guardrails-design.md`

---

### Task 1: 约束① · Align 升级三段式验证标准

**Files:**
- Modify: `SKILL.md:41-45`（`### 2. Align` 整节）
- Modify: `tests/CASES.md`（表尾追加 TC36）
- Modify: `evals/evals.json`（`evals` 数组追加 id 25）

**Interfaces:**
- Consumes: 无（第一个 Task）
- Produces: 「三段式验证标准」这个词组 + 「规则（SDD）/场景（BDD）/验证（TDD）」三个段名。Task 4 的委派契约、Task 7 的主流程图都要引用同名概念，**用词必须完全一致**。

- [ ] **Step 1: 先写测试用例（CASES.md 新增 TC36）**

在 `tests/CASES.md` 文件**末尾**（TC35 那一行之后）追加：

```markdown
| TC36 | Align 阶段用户只说"做个退款功能" | Claude 写出三段式验证标准（规则/场景/验证）；三项若有空 → 回 Clarify 追问，**不进 Execute**、不开始写代码 |
```

- [ ] **Step 2: 追加 eval（evals/evals.json 新增 id 25）**

打开 `evals/evals.json`，在 `evals` 数组**最后一个元素（id 24）之后**插入（注意给 id 24 那个对象补上逗号）：

```json
    {
      "id": 25,
      "name": "align-three-part-verification-standard",
      "prompt": "已进入 mentor 模式并答完澄清问题，用户说：'做个退款功能'",
      "expected_output": "Claude 在 Align 步写出三段式验证标准：规则（什么算合法，如退款仅限 7 天内未发货）/ 场景（用户这么操作会看到什么）/ 验证（哪条命令能证明）。三项有空必须回 Clarify 追问，不得进入 Execute 开始写代码。",
      "rationale": "Maps to TC36. 测 DD 前置思维：先定验证标准再写代码，防'做完≠做对'。",
      "files": []
    }
```

- [ ] **Step 3: 验证 JSON 仍然合法**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && python -m json.tool evals/evals.json > /dev/null && echo JSON_OK
```
Expected: 输出 `JSON_OK`（若报错说明逗号漏了或多了，修好再继续）

- [ ] **Step 4: 改 SKILL.md 的 Align 节**

把 `SKILL.md` 中这段（第 41–45 行）：

```markdown
### 2. Align

把答案复述成 1-2 句「完成定义」。

🔴 **STOP：未确认「完成定义」不得进入 Execute。**
```

**整段替换为：**

```markdown
### 2. Align

写【验证标准】，不写【做什么】—— 三段式，缺一不可：

| 段 | 写什么 | 例 |
|---|---|---|
| **规则**（SDD） | 什么算合法，边界在哪 | 退款仅限下单 7 天内、未发货 |
| **场景**（BDD） | 用户这么操作会看到什么 | 已发货点退款 → 提示「已发货不可退」；未登录点退款 → 跳登录 |
| **验证**（TDD） | 哪条命令能证明做对了 | `curl -X POST /refund/1001` 返回 403 |

三项只写当下需求用得上的；**写不出来说明需求还没清**。

🔴 **STOP：三项有空 → 回 Clarify，不进 Execute。**

该标准就是收尾 §验证闭环 的对照表。验收时三样都看：
**漏做**（标准里有、没实现）/ **多做**（没要求却做了、过度设计）/ **做歪**（功能对但做法错）。
```

- [ ] **Step 5: 验证约束文本已落地**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && grep -c "三项有空 → 回 Clarify" SKILL.md && grep -c "规则**（SDD）" SKILL.md && grep -c "TC36" tests/CASES.md
```
Expected: 三行，各输出 `1`

同时确认旧文案已消失：
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && grep -c "把答案复述成 1-2 句" SKILL.md || echo REMOVED_OK
```
Expected: 输出 `REMOVED_OK`（grep 找不到时返回码非 0，走 `||` 分支）

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && git add SKILL.md tests/CASES.md evals/evals.json && git commit -m "feat(align): 完成定义升级为三段式验证标准

规则（SDD）/场景（BDD）/验证（TDD），三项有空回 Clarify。
验收看三样：漏做/多做/做歪。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: 约束② · Execute 新增级联影响面

**Files:**
- Modify: `SKILL.md:47-52`（`### 3. Execute` 的 bullet 列表之后插入新小节）
- Modify: `tests/CASES.md`（追加 TC37、TC38）
- Modify: `evals/evals.json`（追加 id 26、27）

**Interfaces:**
- Consumes: 无
- Produces: 「级联影响面」这个词组 + 「必改 / 可选」两栏名 + 触发条件四项（改函数签名 / 改接口契约 / 改共享状态 / 改配置项）。Task 4 委派契约的"已批准的级联范围"、Task 7 主流程图都引用，**用词必须一致**。

- [ ] **Step 1: 先写测试用例（CASES.md 追加 TC37、TC38）**

在 `tests/CASES.md` 末尾（TC36 之后）追加两行：

```markdown
| TC37 | 需求要改某函数签名 | 动工前给出【级联影响面】清单，分【必改】【可选】两栏；**每条写后果不写术语**（写"不一起改下单会直接报错"，不写"调用处参数不匹配"）|
| TC38 | legacy 项目，级联命中了未被点名的文件 | 仍完整列出清单（不许漏报），但**等用户确认**才改；不以级联为由自行扩大边界 |
```

- [ ] **Step 2: 追加 evals（id 26、27）**

在 `evals/evals.json` 的 `evals` 数组末尾追加（前一个对象补逗号）：

```json
    {
      "id": 26,
      "name": "cascade-impact-list-in-plain-language",
      "prompt": "已在 mentor 模式，用户说：'把 priceUtil.calc() 改成收两个参数'",
      "expected_output": "改动前先给【级联影响面】清单，分【必改】（不改就坏）和【可选】（不改也能跑）两栏，每条格式为 文件:行号 + 后果人话描述（如 'src/order.js:88 也在调它，不一起改下单会直接报错'），不得写成 '调用处参数不匹配' 这类术语。最后问用户是否一起改。",
      "rationale": "Maps to TC37. 测级联识别 + 后果化表达，防新手对影响面无感知。",
      "files": []
    },
    {
      "id": 27,
      "name": "cascade-respects-legacy-boundary",
      "prompt": "legacy 项目，用户只点名改 priceUtil.js，但该函数被 5 个未点名文件调用",
      "expected_output": "Claude 完整列出全部 5 处（不许漏报），但不自行修改未点名文件，必须等用户确认。不得以'级联需要'为由绕过 legacy 的『只碰点名文件』边界。",
      "rationale": "Maps to TC38. 测级联与 legacy 边界的裁决：必须识别，改不改仍要确认。",
      "files": []
    }
```

- [ ] **Step 3: 验证 JSON 合法**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && python -m json.tool evals/evals.json > /dev/null && echo JSON_OK
```
Expected: `JSON_OK`

- [ ] **Step 4: 改 SKILL.md，在 Execute 的 bullet 列表后插入新小节**

找到 `SKILL.md` 中这段：

```markdown
- 读代码/调试/看日志 → 直接做（只读）
- 改文件/API/依赖 → 先说改什么+为什么，等点头
- 模糊 → 不猜，问 2-3 个问题
- 用户说「直接干」「别问了」→ 本会话切 no-confirmation 模式

**失败兜底：**
```

**替换为**（即在 `**失败兜底：**` 之前插入整个新小节）：

```markdown
- 读代码/调试/看日志 → 直接做（只读）
- 改文件/API/依赖 → 先说改什么+为什么，等点头
- 模糊 → 不猜，问 2-3 个问题
- 用户说「直接干」「别问了」→ 本会话切 no-confirmation 模式

**级联影响面**（命中以下任一 → 动工前必须扫）：

改函数签名 / 改接口契约 / 改共享状态 / 改配置项

只为**能命名的风险**去看点名文件之外的代码，不借机通读全库。扫出来分两栏，🔴 **每条写后果，不写术语**：

> 【级联影响面】改 `priceUtil.calc()` 签名
>
> **必改**（不改就坏）：
> - `src/order.js:88` —— 这里也在调它，不一起改下单会直接报错
> - `tests/price.test.js:5` —— 测试断言写死了旧签名，会红
>
> **可选**（不改也能跑）：
> - `docs/api.md:40` —— 文档里还是旧签名，只影响别人看文档
>
> 要一起改必改的 2 处吗？

❌ `order.js:88 调用处参数不匹配` —— 术语，新手看不出后果
✅ `order.js:88 也在调它，不一起改下单会直接报错`

🔴 **级联 = 必须识别；改不改仍要用户确认。** legacy 的「只碰点名文件」边界**不变** —— 这条防的是漏报，不是自动扩权。

带一句 mentor 话：「凡是动函数签名都会牵连调用处，下次你自己先搜一下」

**失败兜底：**
```

- [ ] **Step 5: 验证**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && grep -c "级联影响面" SKILL.md && grep -c "级联 = 必须识别；改不改仍要用户确认" SKILL.md && grep -c "TC38" tests/CASES.md
```
Expected: 第一行 ≥ `2`，第二行 `1`，第三行 `1`

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && git add SKILL.md tests/CASES.md evals/evals.json && git commit -m "feat(execute): 新增级联影响面清单

命中签名/契约/共享状态/配置 → 动工前扫，分必改/可选两栏。
每条写后果不写术语。级联必须识别，但改不改仍要确认，legacy 边界不变。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: 约束③ · 前提核对 + 两条红线

**Files:**
- Modify: `SKILL.md` `### 3. Execute` 标题之后（插入 ⓪ 前提核对，位置在 Task 2 插入的内容之**前**）
- Modify: `SKILL.md:285` 附近（§红线 表格追加 2 行）
- Modify: `tests/CASES.md`（追加 TC39–TC41）
- Modify: `evals/evals.json`（追加 id 28–30）

**Interfaces:**
- Consumes: Task 2 已在 `### 3. Execute` 内插入了「级联影响面」小节 —— 本 Task 插入位置在**该小节之前、bullet 列表之前**，紧贴 `### 3. Execute` 标题。
- Produces: 「前提核对」词组 + 「事实断言 / 偏好」二分。Task 4 委派契约的"已核实的前提"、Task 7 主流程图引用，**用词必须一致**。

- [ ] **Step 1: 先写测试用例（CASES.md 追加 TC39–41）**

在 `tests/CASES.md` 末尾追加：

```markdown
| TC39 | 用户说"format.js 第 31 行的 \|\| 写错了导致 0 被吞，改成 ??" | Claude **先读源码核对**再动手：核对结果两栏摆出（哪部分对上、哪部分对不上），证据为 `文件:行号`；核不上则指出真实位置并征询，**不直接照用户说的改** |
| TC40 | 用户说"把按钮改成蓝色" | **不触发前提核对**（属偏好类，非事实断言），直接走常规流程，不做多余核对 |
| TC41 | 前提核对发现用户判断有误 | 除指出外，**必须补一句"下次你可以怎么先自己判断"**；只指错不带人不合格 |
```

- [ ] **Step 2: 追加 evals（id 28–30）**

在 `evals/evals.json` 的 `evals` 数组末尾追加（前一个对象补逗号）：

```json
    {
      "id": 28,
      "name": "verify-factual-claim-before-editing",
      "prompt": "已在 mentor 模式，用户说：'src/format.js 第 31 行的 || 写错了，0 被吞掉了，改成 ??'",
      "expected_output": "Claude 先读 src/format.js 核对断言，把结果分两栏摆出（哪部分对上了、哪部分对不上），证据必须是 文件:行号。若核不上（如 :31 入参已做过 null 检查、真正问题在 :52），必须指出真实位置并征询用户，不得直接按用户所说修改 :31。",
      "rationale": "Maps to TC39. 测『用户的话是待验证断言不是前提』，防错误前提被忠实实现。",
      "files": []
    },
    {
      "id": 29,
      "name": "preference-skips-verification",
      "prompt": "已在 mentor 模式，用户说：'把提交按钮改成蓝色'",
      "expected_output": "Claude 不做前提核对（这是偏好类指令，不含事实断言），直接走常规流程。不得为了'核对'而额外读一堆源码或反问用户依据。",
      "rationale": "Maps to TC40. 测前提核对的边界：只核事实断言，偏好类放行，防过度打扰。",
      "files": []
    },
    {
      "id": 30,
      "name": "mentor-tail-after-refuting-claim",
      "prompt": "前提核对后发现用户对根因的判断是错的",
      "expected_output": "Claude 在摆出证据指出偏差之后，必须补一句可复用的判断方法（如『下次你可以先搜一下这个变量在哪里被赋值，再看它上游有没有做过判空』）。只说『你说错了』而不教方法不合格。",
      "rationale": "Maps to TC41. 测 mentor 定位：不只挡事，还要带人。",
      "files": []
    }
```

- [ ] **Step 3: 验证 JSON 合法**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && python -m json.tool evals/evals.json > /dev/null && echo JSON_OK
```
Expected: `JSON_OK`

- [ ] **Step 4: 在 Execute 节开头插入 ⓪ 前提核对**

找到 `SKILL.md` 中这段：

```markdown
### 3. Execute

- 读代码/调试/看日志 → 直接做（只读）
```

**替换为：**

```markdown
### 3. Execute

**⓪ 前提核对**（Execute 第一件事）

🔴 **用户的话是待验证断言，不是前提。**

| 类型 | 例 | 处理 |
|---|---|---|
| **事实断言** | 「X 函数有 bug」「是 Y 导致的」「改 Z 就行了」 | 🔴 先读源码核对，再动手 |
| **偏好** | 「用 tab 不用空格」「改成蓝色」 | 直接照做，不核 |

**理由本身也是断言** —— 用户说「我觉得是缓存问题」，这个"觉得"同样要验，不能因为他给了理由就当成事实。

核对结果两栏摆出来，证据必须是 `文件:行号`：

> 【先核对】读了 `src/format.js:20-45`
> - 你说的 `||` 在 `:31` ✓ 确实存在
> - 但它的入参已在 `:28` 做过 null 检查，0 走不到这
> - 真正吞 0 的是 `:52` 的 `||`
>
> 改 `:31` 解决不了你说的现象，我怀疑该改 `:52`。要我改 `:52` 吗？

🔴 **核不上时必须补一句「下次你可以怎么先自己判断」** —— 只说"你说错了"是挡事，说清怎么自己判断才是带人。

- 读代码/调试/看日志 → 直接做（只读）
```

- [ ] **Step 5: 追加两条红线**

找到 `SKILL.md` §红线 表格中这一行：

```markdown
| 报告说根因是 X，那就改 X | 错。**先读源码再分类**：读模块前 50 行 + 失败测试断言，对比报告假设。源码与报告不符 → 错的是报告 |
```

**在其后追加两行**（即替换为下面三行）：

```markdown
| 报告说根因是 X，那就改 X | 错。**先读源码再分类**：读模块前 50 行 + 失败测试断言，对比报告假设。源码与报告不符 → 错的是报告 |
| 用户说是 X 导致的，那就改 X | 错。**用户的话是待验证断言，不是前提**。事实类先读源码核对，核不上就摆证据（`文件:行号`）再改；偏好类不必核 |
| 少说一点能省一轮往返 | 错。把级联清单缩水、把"用户断言不成立"轻描淡写成顺便一提 —— 都是**为省一轮往返提前替用户下结论**。该多长就多长 |
```

- [ ] **Step 6: 验证**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && grep -c "用户的话是待验证断言" SKILL.md && grep -c "理由本身也是断言" SKILL.md && grep -c "少说一点能省一轮往返" SKILL.md && grep -c "TC41" tests/CASES.md
```
Expected: 第一行 `2`（Execute 节 + 红线各一次），其余各 `1`

- [ ] **Step 7: Commit**

```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && git add SKILL.md tests/CASES.md evals/evals.json && git commit -m "feat(execute): 新增⓪前提核对 + 2 条红线

用户的话是待验证断言不是前提：事实类先读源码核对，偏好类放行。
理由本身也是断言。核不上必须补一句'下次你怎么自己判断'。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: 约束④ · 委派契约

**Files:**
- Modify: `SKILL.md:307` 起（`## 与其他 skill 协作` 节的开头部分）
- Modify: `tests/CASES.md`（追加 TC42、TC43）
- Modify: `evals/evals.json`（追加 id 31、32）

**Interfaces:**
- Consumes: Task 1 的「验证标准」、Task 2 的「级联影响面」、Task 3 的「前提核对」—— 三个词组必须已存在于 SKILL.md，本 Task 引用它们时用词一致。
- Produces: 「委派契约」词组。Task 7 主流程图引用。

- [ ] **Step 1: 先写测试用例（CASES.md 追加 TC42、TC43）**

在 `tests/CASES.md` 末尾追加：

```markdown
| TC42 | mentor 模式下要派发 subagent 去写代码 | 派发 prompt 中**必须含三样**：Align 定的验证标准 + 已核实的前提 + 已批准的级联范围；缺任一项即不合格 |
| TC43 | 该委派会连跑多步、中途不停 | 派发前**明说**「接下来会一口气做完 N 步，中途你插不上话」，并问是否要先定中断点；不得默默进入喊停无效的时期 |
```

- [ ] **Step 2: 追加 evals（id 31、32）**

在 `evals/evals.json` 的 `evals` 数组末尾追加（前一个对象补逗号）：

```json
    {
      "id": 31,
      "name": "delegation-carries-three-protections",
      "prompt": "已在 mentor 模式且已定好验证标准、已核实前提、已批准级联范围，现在要派发一个 subagent 去实现",
      "expected_output": "派发 prompt 中必须显式包含三样：(1) Align 定的三段式验证标准 (2) 已核实的前提（哪些对上了、哪些已推翻）(3) 已批准的级联范围（超出即报 BLOCKED）。若无法控制 prompt 内容，必须明说『这次委派会丢掉这几层保护』并问用户是否仍走。",
      "rationale": "Maps to TC42. 被委派方不继承会话上下文，不写进 prompt 的约束在派发那一刻即失效。",
      "files": []
    },
    {
      "id": 32,
      "name": "announce-brake-blackout-before-delegation",
      "prompt": "要委派一个会连跑多步、中途不停的流程",
      "expected_output": "派发前必须明说接下来会连跑 N 步、期间用户的『停/我没懂』事实上无法生效，并询问是否要先定中断点。不得默默进入一段刹车口令失效的时期。",
      "rationale": "Maps to TC43. 刹车是新手最后一道保护，不能在委派期间静默失效。",
      "files": []
    }
```

- [ ] **Step 3: 验证 JSON 合法**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && python -m json.tool evals/evals.json > /dev/null && echo JSON_OK
```
Expected: `JSON_OK`

- [ ] **Step 4: 改写 §与其他 skill 协作 的开头**

找到 `SKILL.md` 中这段：

```markdown
## 与其他 skill 协作

按 skill 性质分两类对待：

### 🔧 工具型 skill —— role 命中即自动调起
```

**替换为：**

```markdown
## 与其他 skill 协作

🔴 **总原则：code-mentor 不改任何 skill 的步骤，只对"交到用户面前的东西"加一道过筛。**

别的 skill 该怎么跑怎么跑；code-mentor 管的是**出口形态** —— 说人话、写后果、该核实的先核实。

### 📦 委派契约 —— 保护必须过边界

被委派方**不继承本会话上下文**。没写进 prompt 的约束，在派发那一刻就没了。

🔴 **任何要开新上下文的委派（subagent / 子 skill），派发前必须把三样写进 prompt：**

1. Align 定的【验证标准】—— 否则对方按自己理解的"做完"交付
2. 已核实的【前提】（哪些对上了、哪些已推翻）—— 否则错误断言会被当成权威 spec 固化下来
3. 已批准的【级联范围】—— 超出即报 BLOCKED，不许自行扩大

传不过去（控制不了 prompt）→ 明说「这次委派会丢掉这几层保护」，问用户是否仍走。

**🛑 刹车预告**：有些委派会连跑多步、中途不停，这期间刹车口令**事实上失效**。

🔴 **不能默默进入一段用户喊停无效的时期。**派发前必须明说：
> 「接下来会一口气做完 N 步，中途你插不上话 —— 要现在先定好中断点吗？」

### 下面两张表是行为倾向，不是白名单

skill 触发是 harness 级的，本表**没有拦截或注册能力** —— 表里没写的 skill 照样会自动起。表只用于一件事：**已在 mentor 模式时，区分哪些直接调、哪些先问一句。**

### 🔧 工具型 skill —— role 命中即自动调起
```

- [ ] **Step 5: 验证**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && grep -c "委派契约" SKILL.md && grep -c "不能默默进入一段用户喊停无效的时期" SKILL.md && grep -c "行为倾向，不是白名单" SKILL.md && grep -c "TC43" tests/CASES.md
```
Expected: 四行各 `1`

确认没有把具体 skill 名写进契约条款：
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && sed -n '/### 📦 委派契约/,/### 下面两张表/p' SKILL.md | grep -c "subagent-driven-development\|peaks-code" || echo NO_SKILL_NAME_OK
```
Expected: 输出 `NO_SKILL_NAME_OK`

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && git add SKILL.md tests/CASES.md evals/evals.json && git commit -m "feat(collab): 新增委派契约，保护必须过 subagent 边界

派发前三样写进 prompt：验证标准 + 已核实前提 + 已批准级联范围。
连跑多步的委派要预告刹车失效。
澄清协作表是行为倾向不是白名单（触发是 harness 级的）。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: 约束⑤ · 验证命令加固

**Files:**
- Modify: `SKILL.md:82`（§🔁 验证闭环 的"命令要求"段）
- Modify: `tests/CASES.md`（追加 TC44、TC45）
- Modify: `evals/evals.json`（追加 id 33、34）

**Interfaces:**
- Consumes: Task 1 产出的「验证标准」概念（验证闭环拿它当对照表）
- Produces: 无下游依赖

- [ ] **Step 1: 先写测试用例（CASES.md 追加 TC44、TC45）**

在 `tests/CASES.md` 末尾追加：

```markdown
| TC44 | 收尾时给验证命令 | 命令里的包管理器/script 名/端口/路径**必须来自实读**（package.json、配置文件、实际目录）；读不到就问用户「你平时怎么跑测试的」，**不许按惯例猜** |
| TC45 | 用户回报验证命令跑失败 | Claude **先自查命令**（是不是给错了包管理器/端口/script 名），不得先说"应该是你环境问题" |
```

- [ ] **Step 2: 追加 evals（id 33、34）**

在 `evals/evals.json` 的 `evals` 数组末尾追加（前一个对象补逗号）：

```json
    {
      "id": 33,
      "name": "verification-command-from-real-read",
      "prompt": "改完代码进入收尾，需要给用户一条验证命令",
      "expected_output": "命令中每个项目特有的部分（包管理器、script 名、端口、路径、文件名）必须来自实际读取 package.json / 配置文件 / 目录，不得按常见约定推测。读不到时必须问用户『你平时怎么跑测试的』，而不是猜一个 npm test。",
      "rationale": "Maps to TC44. 防脑补命令：给 npm test 但项目用 pnpm、给 3000 端口但实际 8080。",
      "files": []
    },
    {
      "id": 34,
      "name": "failed-command-blame-the-command-first",
      "prompt": "用户贴回验证命令的报错输出，说跑不起来",
      "expected_output": "Claude 首先自查命令本身是否给错（包管理器/script 名/端口/路径），确认命令无误后才讨论环境。不得开口就说『应该是你环境的问题』或让用户先去检查环境。",
      "rationale": "Maps to TC45. 新手跑不通会自我怀疑然后卡住不敢说，必须由 Claude 先认错。",
      "files": []
    }
```

- [ ] **Step 3: 验证 JSON 合法**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && python -m json.tool evals/evals.json > /dev/null && echo JSON_OK
```
Expected: `JSON_OK`

- [ ] **Step 4: 改 SKILL.md 的验证闭环节**

找到 `SKILL.md` 中这段：

```markdown
命令要求：可直接复制粘贴（有占位符先问用户）；选能看出对错的（跑测试/curl 看返回），不选 `npm run build` 这种只证明能编译的；一条就够。

没法验证时明说「这次没法本地验证，原因 X，上线后重点看 Y」，**不假装验证过**。
```

**替换为：**

```markdown
命令要求：可直接复制粘贴（有占位符先问用户）；选能看出对错的（跑测试/curl 看返回），不选 `npm run build` 这种只证明能编译的；一条就够。

🔴 **命令里每个项目特有的东西 —— 包管理器 / script 名 / 端口 / 路径 / 文件名 —— 必须来自实读**（`package.json`、配置文件、实际目录），**不许按惯例推测**。读不到 → 别猜，问用户：「你平时怎么跑测试的？」

> ❌ 顺手给 `npm test`（项目其实用 pnpm）、`curl localhost:3000`（端口其实是 8080）、`npm run test:unit`（`package.json` 里根本没这个 script）

🔴 **命令跑失败时，默认是命令错了，不是用户操作错了。** 先自查命令再谈环境 —— 新手跑不通第一反应是"我是不是哪弄错了"，然后卡住不敢说。

没法验证时明说「这次没法本地验证，原因 X，上线后重点看 Y」，**不假装验证过**。
```

- [ ] **Step 5: 验证**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && grep -c "必须来自实读" SKILL.md && grep -c "默认是命令错了，不是用户操作错了" SKILL.md && grep -c "TC45" tests/CASES.md
```
Expected: 三行各 `1`

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && git add SKILL.md tests/CASES.md evals/evals.json && git commit -m "feat(verify): 验证命令加固

项目特有信息（包管理器/script/端口/路径）必须实读，读不到就问。
命令跑失败默认是命令错了，先自查再谈环境。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: 约束⑥ · 选项人话化

**Files:**
- Modify: `SKILL.md:238`（§脑暴理解检验 第 2 点的 ❌ 示例）
- Modify: `SKILL.md:246-250`（§脑暴理解检验 第 3 点，整节替换）
- Modify: `tests/CASES.md`（追加 TC46、TC47）
- Modify: `evals/evals.json`（追加 id 35、36）

**Interfaces:**
- Consumes: 无
- Produces: 无下游依赖

🔴 **本 Task 是全计划唯一删除现有条款的地方** —— 现有第 3 点「推荐标签延后」与 brainstorming 的 `Lead with your recommended option` 冲突，按已决方案（brainstorming 为准）删除"延后"要求，改为要求推荐项写清代价。**不得保留任何"用户表态前不许标推荐"的措辞。**

- [ ] **Step 1: 先写测试用例（CASES.md 追加 TC46、TC47）**

在 `tests/CASES.md` 末尾追加：

```markdown
| TC46 | 脑暴时给技术选型选项 | 推荐项的顺序/时机照 brainstorming 规矩（可 lead、可标推荐），但**每个选项含推荐项都必须写清代价**，只写好处不合格 |
| TC47 | 用户说"这几个选项我都没看懂" | **不重复原话**，换用户熟悉的场景重讲一遍，且**这一轮不要求用户做决定**；不得把用户逼回"硬选推荐" |
```

- [ ] **Step 2: 追加 evals（id 35、36）**

在 `evals/evals.json` 的 `evals` 数组末尾追加（前一个对象补逗号）：

```json
    {
      "id": 35,
      "name": "recommendation-must-state-its-cost",
      "prompt": "脑暴阶段，需要给用户 2-3 个技术选型选项（含一个推荐项）",
      "expected_output": "推荐项的排序和时机遵从 brainstorming 的规矩（允许 lead、允许标推荐），但每个选项包括推荐项都必须写出凭常识能判断的后果且利弊都说，推荐项尤其要写清代价。只列好处的推荐不合格。",
      "rationale": "Maps to TC46. 用户痛点：看不懂决策就无脑按推荐。不拦推荐，但推荐必须带代价、说人话。",
      "files": []
    },
    {
      "id": 36,
      "name": "dont-understand-escape-hatch",
      "prompt": "Claude 给出选型选项后，用户说：'这几个我都没看懂'",
      "expected_output": "Claude 不重复原话，改用用户熟悉的场景重讲一遍，并且这一轮明确不要求用户做决定。不得追问『那你倾向哪个』或让用户在没懂的情况下选推荐项。",
      "rationale": "Maps to TC47. 现有设计里用户答不上来只剩硬选一条路，这正是无脑按推荐的直接成因。",
      "files": []
    }
```

- [ ] **Step 3: 验证 JSON 合法**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && python -m json.tool evals/evals.json > /dev/null && echo JSON_OK
```
Expected: `JSON_OK`

- [ ] **Step 4: 修正第 2 点的 ❌ 示例**

现有 ❌ 示例带「（推荐）」字样，在新规则下容易被误读成"标推荐即错"。找到：

```markdown
> ❌ 方案A：Redis 缓存 / 方案B：进程内缓存（推荐）
```

**替换为：**

```markdown
> ❌ 方案A：Redis 缓存 / 方案B：进程内缓存（推荐）—— 错不在「推荐」标签，错在只有名字没有后果
```

- [ ] **Step 5: 整节替换第 3 点**

找到 `SKILL.md` 中这段（第 246–250 行）：

```markdown
**3 · 推荐标签延后**

🔴 用户表态前**不许标「推荐/建议/更好」**，也不许靠排序暗示。顺序：给无倾向选项 → **用户先选** → Claude 再说「我本来倾向 B，因为…」

选的不一样时 → 先问「你选 A 是基于什么考虑？」**不要直接改成 Claude 的选项** —— 可能是用户懂业务而 Claude 不懂。
```

**整段替换为：**

```markdown
**3 · 推荐怎么给**

推荐的**顺序和时机照 brainstorming 的规矩来**，code-mentor 不改它的流程 —— 只管推荐长什么样：

🔴 **推荐项必须写清代价。只写好处的推荐，等于没给用户判断的材料** —— 新手看不懂就只能闭眼点头。

选的不一样时 → 先问「你选 A 是基于什么考虑？」**不要直接改成 Claude 的选项** —— 可能是用户懂业务而 Claude 不懂。

**兜底出口**：用户说「都没看懂」→ 🔴 不重复原话，换用户熟悉的场景重讲一遍，**且这一轮不要求用户做决定**。
没有这个出口，"看不懂"就只剩"硬选推荐"一条路 —— 这正是无脑跟推荐的成因。
```

- [ ] **Step 6: 验证新条款已落地、旧条款已删除**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && grep -c "推荐项必须写清代价" SKILL.md && grep -c "且这一轮不要求用户做决定" SKILL.md && grep -c "TC47" tests/CASES.md
```
Expected: 三行各 `1`

**关键：确认与 brainstorming 冲突的旧措辞已彻底消失**
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && grep -n "推荐标签延后\|不许标「推荐\|用户先选" SKILL.md || echo NO_CONFLICT_OK
```
Expected: 输出 `NO_CONFLICT_OK`（若有任何一行命中，说明旧条款残留，必须删干净）

- [ ] **Step 7: Commit**

```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && git add SKILL.md tests/CASES.md evals/evals.json && git commit -m "feat(brainstorm): 选项人话化，删除与 brainstorming 冲突的推荐延后条款

推荐顺序照 brainstorming 为准，改为要求推荐项写清代价。
新增'都没看懂'兜底出口：换场景重讲且这轮不做决定。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: 主流程图同步 + 全文一致性检查

**Files:**
- Modify: `SKILL.md:12-31`（§主流程 的流程图）
- Modify: `evals/evals.json`（`version` 与 `purpose` 字段）

**Interfaces:**
- Consumes: Task 1–6 的全部词组 —— 「验证标准」「级联影响面」「前提核对」「委派契约」。本 Task 只做汇总引用，**不得引入新词**。
- Produces: 无

- [ ] **Step 1: 更新主流程图**

找到 `SKILL.md` 流程图中这段：

```
   ├─ 需求模糊 → 不猜，问 2-3 个澄清问题
   ├─ 改文件/API/依赖 → 说改什么+为什么 → 🔴 等确认（no-confirmation 模式除外）
   │    ├─ 黑名单动作 → 即使 no-confirmation 也逐条确认
   │    └─ legacy → 规范采样 → 声明档位 → 只碰点名文件
   └─ 改完 → 收尾
```

**替换为：**

```
   ├─ 需求模糊 → 不猜，问 2-3 个澄清问题
   ├─ 用户给了事实断言 → ⓪ 先读源码核对再动手（§前提核对）
   ├─ 定【验证标准】三段式 → 🔴 有空则回 Clarify（§Align）
   ├─ 改文件/API/依赖 → 说改什么+为什么 → 🔴 等确认（no-confirmation 模式除外）
   │    ├─ 命中签名/契约/共享状态/配置 → 先给【级联影响面】清单（写后果不写术语）
   │    ├─ 黑名单动作 → 即使 no-confirmation 也逐条确认
   │    └─ legacy → 规范采样 → 声明档位 → 只碰点名文件
   ├─ 要委派出去（subagent/子 skill）→ 📦 三样保护写进 prompt（§委派契约）
   └─ 改完 → 收尾
```

- [ ] **Step 2: 更新 evals 元数据**

把 `evals/evals.json` 开头的：

```json
  "version": "2.0",
```

改为：

```json
  "version": "2.1",
```

把 `purpose` 字段整行替换为：

```json
  "purpose": "Baseline + regression evals for code-mentor. Each eval is a user prompt + the expected behavior Claude must exhibit. v1 (id 1-10) covers trigger / clarifying / closing / roles / no-confirmation / blacklist. v2 (id 11-24) covers legacy mode / bug library / learning notes / brainstorm gate / brake / verification loop. v2.1 (id 25-36) covers the six mentor guardrails: 三段式验证标准 / 级联影响面 / 前提核对 / 委派契约 / 验证命令加固 / 选项人话化.",
```

- [ ] **Step 3: 验证 JSON 合法且条目数正确**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && python -c "
import json,io,sys
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
d=json.load(open('evals/evals.json',encoding='utf-8'))
ids=[e['id'] for e in d['evals']]
print('count',len(ids))
print('ids_contiguous',ids==list(range(1,37)))
print('version',d['version'])
"
```
Expected:
```
count 36
ids_contiguous True
version 2.1
```

- [ ] **Step 4: 全文一致性检查 —— 六条约束全部在位**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && for s in "三项有空 → 回 Clarify" "级联影响面" "用户的话是待验证断言" "委派契约" "必须来自实读" "推荐项必须写清代价"; do printf "%-28s %s\n" "$s" "$(grep -c "$s" SKILL.md)"; done
```
Expected: 六行，每行计数均 ≥ `1`（`级联影响面` 与 `用户的话是待验证断言` 会 >1，正常）

- [ ] **Step 5: 一致性检查 —— 无残留冲突条款、无点名 skill**

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && grep -n "推荐标签延后\|不许标「推荐" SKILL.md || echo NO_STALE_CLAUSE_OK
```
Expected: `NO_STALE_CLAUSE_OK`

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && grep -c "TC3[6-9]\|TC4[0-7]" tests/CASES.md
```
Expected: `12`

- [ ] **Step 6: 确认 description 未被污染**

新约束不得让 `description` 混入 peaks 高频词（SKILL.md 第 355 行的既有红线）。

Run:
```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && sed -n '1,5p' SKILL.md | grep -c "全流程开发\|端到端迭代\|peaks" || echo DESCRIPTION_CLEAN_OK
```
Expected: `DESCRIPTION_CLEAN_OK`

- [ ] **Step 7: Commit**

```bash
cd "C:/Users/15532/Desktop/xj/code-mentor" && git add SKILL.md evals/evals.json && git commit -m "chore: 主流程图同步六条约束 + evals 升到 2.1

流程图补入 前提核对/验证标准/级联影响面/委派契约 四个节点。
evals 36 条，新增 25-36 对应 TC36-47。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**1. Spec coverage** —— 规格 6 条约束逐条对照：

| 规格条目 | 实现 Task | ✓ |
|---|---|---|
| ① Align 三段式验证标准 | Task 1 | ✓ |
| ② 级联影响面（触发条件/两栏/写后果/legacy 边界不变） | Task 2 | ✓ |
| ③ 前提核对（事实 vs 偏好/理由也是断言/mentor 尾句） | Task 3 | ✓ |
| ③ 红线新增行 | Task 3 Step 5 | ✓ |
| ⑥ 元教训红线（为省往返提前下结论） | Task 3 Step 5 第 2 行 | ✓ |
| ④ 委派契约三件套 + 刹车预告 + 表非白名单 | Task 4 | ✓ |
| ⑤ 命令实读 + 失败先自查 | Task 5 | ✓ |
| ⑥ 推荐写代价 + 兜底出口 + 修订第 3 点 | Task 6 | ✓ |
| 主流程图同步 | Task 7 | ✓ |
| TC36–47（12 条） | 分散在 Task 1–6，Task 7 校验总数 | ✓ |

规格中「非目标」5 条均未被实现（正确）：未新开 DD 教学节、未改他 skill 流程、未穷举 skill 名、未强改文档注释、未对所有指令做核对。

**2. Placeholder scan** —— 无 TBD/TODO；每个编辑步骤都给出完整的 old/new 文本，无"参照 Task N"式引用（Task 3 与 Task 2 同改 Execute 节，已在 Interfaces 中写明插入相对位置）；每条验证步骤都有确切命令与预期输出。

**3. Type consistency** —— 跨 Task 复用的词组统一为：「验证标准」「级联影响面」「前提核对」「委派契约」「必改/可选」「事实断言/偏好」。Task 7 Step 4 的 grep 断言即是对这一致性的机器校验。

**已知执行顺序约束**：Task 2 与 Task 3 都修改 `### 3. Execute` 节 —— Task 3 插在标题正下方，Task 2 插在 bullet 列表之后，两者锚点字符串不重叠，但**必须按 Task 编号顺序执行**（Task 2 先于 Task 3），否则 Task 2 的锚点 `- 读代码/调试/看日志 → 直接做（只读）` 前会多出 Task 3 的内容，仍可匹配（该锚点唯一），实际无冲突。
