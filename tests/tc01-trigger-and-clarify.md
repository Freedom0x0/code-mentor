# TC1 — Trigger + Clarify

## Scenario

You are Claude with the `code-mentor` skill loaded. The user sends this single message:

> 帮我写个登录

## Verification Checklist (Claude must do all of these)

- [ ] Ask "要不要进入陪跑模式？" before doing anything else
- [ ] After user confirms, ask the 3 clarifying questions:
  - 1. What is the task?
  - 2. What does "done" look like (acceptance criteria)?
  - 3. Which files / modules are involved?
- [ ] **Not** start editing any file
- [ ] **Not** volunteer code, framework suggestions, or "best practice" essays
- [ ] **Not** assume the user knows terminology

## Failure Signals (any of these = test fails)

- Claude starts writing code immediately
- Claude asks only 1 or 2 clarifying questions (missing any of the 3)
- Claude suggests a stack/framework before the user has answered
- Claude asks "你想要什么" type questions that don't map to the 3 fixed slots
