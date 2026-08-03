## Test Cases

Run each test case as a subagent prompt. Each case lists its scenario and the expected behavior Claude must exhibit.

| TC# | Scenario | Expected behavior |
|-----|----------|-------------------|
| TC1 | User says "帮我写个登录" | Claude must first ask whether to enter mentor mode, then ask the 3 clarifying questions; must not start editing |
| TC2 | After clarifying, user says "别问了直接干" | Claude must immediately switch to no-confirmation mode for the rest of the session |
| TC3 | After editing, user says "继续" | Claude must do the closing (light or full per scenario) before asking the next step |
| TC4 | User asks "这是啥" (already in mentor mode) | Claude switches to Patient teacher role, gives a concrete example, does not assume terminology |
| TC5 | Claude spots ambiguous requirements | Does not guess; asks 2–3 clarifying questions |
| TC6 | User says "用陪跑模式" but the task is an email | Claude politely notes the task does not look like development and asks whether to switch back to normal mode |
| TC7 | User says "老板让我做新需求 X，但我不知道从哪下手" | Claude recognizes the brainstorming scenario, **suggests** brainstorming (does not auto-invoke), waits for user nod |
| TC8 | User describes a debugging scenario in mentor mode | Claude switches to Rigor排查助手 role; may suggest systematic-debugging skill |
| TC9 | User only asks "这是啥" (no edit intent) | Claude does NOT trigger mentor mode; answers normally |
| TC10 | User changes 1 file, 5-line typo | Claude uses light closing (one-sentence recap + verification), does not force full closing |
| TC11 | User changes 3 files + 1 API | Claude auto-detects "multi-file + API change", uses full closing |
| TC12 | User is already in `/peaks-code` pipeline | code-mentor does not take over; if user says "切到 peaks" inside mentor mode, code-mentor explicitly suggests switching to peaks-code |
| TC13 | User describes "老板让我做新需求 X，5 个模块，要走完整开发" | Claude recognizes this exceeds mentor mode scope and suggests peaks-code; does not force-fit into mentor mode |
| TC14 | 首次在某目录进 mentor 模式，目录有 200 提交 + CI 配置 | Claude 扫信号给初判，**问用户确认**项目身份；不自行认定；确认后写 `project.md` |
| TC15 | 同一目录第二次进 mentor 模式 | Claude 直接读 `project.md`，**不重复问**项目身份 |
| TC16 | legacy 项目，改一个函数的 3 行取值逻辑 | Claude 声明「A 类 · 行级停用」，注释掉原行并保留，新行写在下面；不删除老代码 |
| TC17 | legacy 项目，需要改函数签名 | Claude 声明「B 类 · 新函数」，整体注释旧函数，写新函数并改调用处 |
| TC18 | legacy 项目，改 A 函数时发现旁边 B 函数有 bug | Claude **不改 B**，登记到 `findings.md`，收尾时询问是否另开一次 |
| TC19 | legacy 项目，老代码用了过时写法，Claude 想按最佳实践写 | Claude 照 `conventions.md` 的既有习惯写；想改风格只登记 findings |
| TC20 | legacy 项目本次有编辑，走 light closing | 即使 light，也追加「影响面清单」：停用清单 + 回滚方式 + findings 新增 |
| TC21 | legacy 项目，要改一个被 20 处调用的核心函数 | 三档均不适用 → Claude 停下说明困境并给选项，**不自行发挥** |
| TC22 | greenfield 项目 | 不加载老项目模式约束，走常规 4 步流程 |
| TC23 | 用户报一个 bug 库里有类似记录的错误 | 排查助手 Step 0-A 先搜 INDEX，命中后先说「你 X 时候遇过，根因 Y，先试 Z」，再走常规排查 |
| TC24 | 排查 3 轮才找到非显然根因 | 收尾时**问用户**「要不要入库」，不自动写；入库后 INDEX 同步更新 |
| TC25 | 手滑打错变量名导致的报错 | **不入库**（根因显然、1 轮解决），不打扰用户 |
| TC26 | 本次改动用到用户没接触过的概念 | 触发 `knowledge` skill（不写 `t000N-X.md`）；知识沉淀已委托给 knowledge 落地到 Obsidian vault |
| TC27 | 脑暴时 Claude 给技术选型选项 | 选项写成后果（"将来加服务器要推倒重写"），**不写抽象形容词**，**不标推荐** |
| TC28 | 用户在脑暴中选了 Claude 不倾向的方案 | Claude 先问「你基于什么考虑」，不直接改成自己的选项 |
| TC29 | 理解检验时用户答不上来 | 换说法讲一遍**然后直接给答案**，不重问、不卡死、不评判 |
| TC30 | 脑暴中定了技术选型 | 写入 `DECISIONS.md`，含「什么时候该推翻」的触发条件 |
| TC31 | 用户中途说「停，我没懂」 | 立即停止推进，换方式重讲，**不说"这很简单"/"刚才说过"**；no-confirmation 模式下同样生效 |
| TC32 | Claude 改完代码 | 给一条可直接复制粘贴的验证命令，**等用户贴回输出**才宣布完成；不说"应该没问题" |
| TC33 | 改的是文档，本地无法验证 | 明说「这次没法本地验证，原因 X，上线后重点看 Y」，不假装验证过 |
| TC34 | 已在 mentor 模式，用户说"这个报错反复出现"或"调了好几轮还是不对" | role=排查助手命中后**自动**调起 `systematic-debugging`，不先问「要不要启动？」 |
| TC35 | 已在 mentor 模式，用户说"老板让我做新需求 X，从哪下手" | code-mentor **不**自动调 brainstorming；问一句「要启动 brainstorming 吗？」等你点头 |
| TC36 | Align 阶段用户只说"做个退款功能" | Claude 写出三段式验证标准（规则/场景/验证）；三项若有空 → 回 Clarify 追问，**不进 Execute**、不开始写代码 |