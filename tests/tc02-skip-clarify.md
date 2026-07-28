# TC2 — Skip Clarify (No-Confirmation Mode)

## Scenario

You are Claude with the `code-mentor` skill loaded. The user has already answered the 3 clarifying questions. After your restated "完成定义", the user says:

> 别问了直接干

## Verification Checklist

- [ ] Acknowledge the switch to no-confirmation mode (1 sentence, e.g. "好，直接干模式，我会在每次改动前说明改了什么，但不再等你点头。")
- [ ] Do not ask any more clarifying questions for the rest of the session
- [ ] For the next file change:
  - [ ] Still do the **pre-edit explanation** (改哪里 + 为什么 + 注意点) — only skip the confirmation wait
  - [ ] Make the edit
  - [ ] Still do the **post-edit teach-back** (核心改动点 + 原理解释) — teach-back is NOT removed in no-confirmation mode
- [ ] When the change is done, perform the closing (light or full per scenario)
- [ ] After closing, ask "下一步做什么？"

## Failure Signals

- Claude continues asking for confirmation on every change after "直接干"
- Claude says "我直接干了" with no pre-edit explanation and no teach-back
- Claude skips both pre-edit and teach-back (mistakenly treats no-confirmation as no-explanation)
- Claude performs no closing at all
