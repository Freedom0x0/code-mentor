# TC3 — Teach-back + Closing Before Continue

## Scenario

You are Claude with the `code-mentor` skill loaded. The user asked you to change a file; you have made the edit. The user now says:

> 继续

## Verification Checklist

- [ ] Do NOT immediately start the next change
- [ ] First, deliver the **post-edit teach-back** (before closing):
  - [ ] 核心改动点（一句话，指代具体代码）
  - [ ] 原理解释（类比或口语举例）
  - [ ] 新概念标注（如果改动引入了新术语或模式）
- [ ] Then, perform closing (light or full per the scope rules in SKILL.md):
  - Light: one-sentence recap + how to verify
  - Full: recap + verification + interface/context (required for multi-file/API)
- [ ] After closing, ask "下一步做什么？"

## Failure Signals

- Claude starts editing the next file with no teach-back and no closing
- Claude does closing but skips the teach-back entirely
- Claude performs full closing on a 5-line typo (over-reach; should be light)
- Claude performs only a partial closing (e.g., recap without verification)
