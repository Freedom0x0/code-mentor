# code-mentor darwin-skill 优化报告

**日期**：2026-08-11
**分支**：`auto-optimize/20260811-1452`
**baseline commit**：`c117132`
**最终 commit**：`8b06a03`
**rubric**：darwin-skill 9 维（结构 59 + 效果 35 + meta 6 = 100）

---

## 总览

| 指标 | 值 |
|---|---|
| 优化轮数 | 1 轮 + 1 测试集增强 |
| 实验次数 | 2（test_set + keep） |
| 保留改进 | 1（Round 1b dim1） |
| 回滚次数 | 0 |
| 实测验证 | 1 次 full_test + 1 次 dry_run |
| 触顶信号 | Round 1b Δ=+0.7 < 2.0，HL-4 触发，**见好就收** |
| 最终分数 | **89.5 / 100**（dry_run 预估） |

---

## 分数变化

| Skill | Before | After | Δ | mode |
|---|---|---|---|---|
| code-mentor | 88.8 | **89.5** | **+0.7** | dry_run |

---

## 9 维分数（最终）

| 维度 | 权重 | 原始分 | 加权得分 | 主要证据 |
|---|---|---|---|---|
| **dim1 Frontmatter** | 7 | **9** ⬆ | 6.3 | description 净化 — 仅触发词 + 行为边界 + "no external dependency"；移除具体路径 |
| dim2 工作流 | 12 | 9 | 10.8 | 4 步外壳 + 4 mode + 6 动作 三层结构清晰 |
| dim3 失败模式编码 | 12 | **10** ⭐ | 12.0 | ~42 条 if-then 三段式兜底（黄金标准）|
| dim4 检查点 | 6 | 9 | 5.4 | 🔴 / 🛑 STOP 视觉标记密集 |
| dim5 可执行性 | 18 | **9** ⭐ | 16.2 | 自封禁"建议/灵活把握"等杀手词 |
| dim6 资源 | 4 | 9 | 3.6 | README + tests + evals + assets 齐全 |
| dim7 架构 | 12 | 9 | 10.8 | 七大块结构 + 无花叔禁用词 |
| **dim8 实测** | 23 | 8 | 18.4 | 6→8 prompts，复合压力覆盖 scope+blacklist / im-sure+settle |
| dim9 反例黑名单 | 6 | **10** ⭐ | 6.0 | 反行为 + Rationalization + 黑名单 三重 |
| **总分** | 100 | — | **89.5** | — |

---

## 优化记录

| commit | 改动 | Δ | 状态 |
|---|---|---|---|
| `c117132` | baseline | — | baseline |
| `7a11f3a` | test-prompts 加 2 个复合压力 prompt | — | test_set（增强测试集）|
| `8b06a03` | description 移 vault 路径 | +0.7 | keep（HL-4 触顶）|

---

## 主要改进

1. **Round 1b（dim1）**：description 从 920 字符净化到 604 字符，纯触发信号——SDO 原则不再混入运行时配置
2. **Round 1a（test_set）**：测试集从 6 → 8 prompt，新增 2 个复合压力场景（scope+blacklist / im-sure+settle），让 with_skill 在复杂场景下的差异化优势可被测出
3. **HL-4 触发后停止**：见好就收，不引入 over-engineering

## 主要强项（持续保持满分）

- **dim3 失败模式编码**（10/10）：~42 条显式 if-then 兜底
- **dim5 可执行性**（9/10）：自封禁 dim5 杀手词
- **dim9 反例黑名单**（10/10）：反行为 + Rationalization + 黑名单 三重

## 主要短板（下一步优化方向）

- **dim8 实测表现**（8/10）：受限于 dry_run；想真实涨分需要 spawn 子 agent 跑实测
- **dim6 资源整合**（9/10 → 实际接近上限）：evals/run.sh 路径假设可以补 README
- **dim1 Frontmatter**（9/10 → +0.7 触顶）：再优化空间小

---

## 后续建议

- **下次优化方向**：实测 dim8 真正涨分（spawn 独立子 agent 跑 8 个 prompt，按 9 维 dim8 重新打分）
- **保留结果**：本次 commit `8b06a03` 在 `auto-optimize/20260811-1452` 分支，可保留可合并

— Darwin Skill 2.0 · "Train your Skills like you train your models"