# PRD: Execute 节加入教学式讲解 + 结构化 skill 推荐

## 需求描述

用户希望 code-mentor 在每次修改代码时，像老师一样讲解（不仅仅"说一句改了什么"），
同时在合适时机主动推荐启动某个 skill，并附上推荐理由，最后向 developer 征求意见。

## 功能拆解

### T1 — 教学式讲解（Execute 节 + 改动前/后均有）

**改动前（pre-edit 说明）：**
在当前 "first state what you will change and why" 基础上，扩展为：
1. 说清楚改哪里（文件 + 行/函数）
2. 解释为什么这样改（设计原因），而非只说"什么"
3. 预告可能的副作用或需要注意的地方（如有）

**改动后（post-edit 讲解，紧随编辑之后，在 Close 之前）：**
每次编辑完成后，在走 Close 之前，先做一段 "teach-back"：
1. 指出改动的核心点（1-2 句）
2. 解释这个改法背后的原因或原则（类比、口语化）
3. 如果引入了新概念/模式，用"用人话说"风格举一个具体小例子

**格式要求：**
- 用口语化语言（默认），不要 essay 风格
- 适当使用类比
- 首次出现的术语必须标注解释
- 用户可以说"详细讲" / "少说点" 调节讲解粒度（session 级别持久）

### T2 — 结构化 skill 推荐（Skill Collaboration 节扩展）

在合适时机主动向用户推荐启动 skill，格式固定：
```
💡 我建议启动 [skill名]
   原因：[1-2 句说明为什么这个场景适合该 skill]
   要启动吗？（说"启动"或"算了"）
```

触发时机（在现有 Recognized Suggestion Scenarios 基础上）：
- 原有的 4 个场景继续触发推荐
- **新增**：每次改动后的 teach-back 阶段，若改动引入了新模式/技术，在 teach-back 末尾也可以推荐（不强制，看改动复杂度）

### T3 — 同步更新 Test Cases（TC2/TC3/TC4）

- TC2：no-confirmation 模式下 teach-back 仍应存在（只省略等待确认，不省略讲解）
- TC3：收尾前的 teach-back 是新增强制步骤，测试应覆盖
- TC4：Patient teacher role 和 teach-back 不重叠 — teacher role 用于纯解释，teach-back 用于改动后

## 不在范围内

- 修改 Roles 表的触发词
- 修改 Red Lines 逻辑
- 修改 High-Risk Blacklist
- 改变 Close 节的结构（teach-back 在 Close 之前，不合并进去）

## 验收标准

- [ ] §3. Execute 包含 pre-edit 教学说明的 3 要素
- [ ] §3. Execute 或新增 §3.5 包含 post-edit teach-back 的 3 要素
- [ ] teach-back 有粒度控制说明（"详细讲" / "少说点"）
- [ ] Skill Collaboration 节有推荐固定格式模板
- [ ] "推荐适当时机"在 Skill Collaboration 节有说明
- [ ] TC2 测试文件更新（no-confirmation 模式下 teach-back 仍保留）
- [ ] TC3 测试文件更新（覆盖 teach-back 在 Close 之前）
- [ ] TC4 测试文件更新（区分 teacher role 和 teach-back）
