# TC6 — Wrong Context (Email Task)

## Scenario

You are Claude with the `code-mentor` skill loaded. The user says:

> 用陪跑模式帮我写一封给老板的邮件，汇报本周进度

## Verification Checklist

- [ ] Politely note: "这个任务看起来不是开发场景，要不要切回普通模式？"
- [ ] Do NOT start asking the 3 clarifying questions as if this were a dev task
- [ ] Wait for the user's decision before proceeding

## Failure Signals

- Claude enters full mentor mode and starts "clarifying" the email
- Claude forces the user through the 4-step workflow for a non-dev task
- Claude silently switches to plain mode without asking