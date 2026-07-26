# TC7 — Suggest Brainstorming

## Scenario

You are Claude with the `code-mentor` skill loaded. The user says:

> 老板让我做新需求 X，让我加一个支付功能，但我不知道从哪下手

## Verification Checklist

- [ ] Switch to Responsible guide role
- [ ] Identify this as a brainstorming scenario
- [ ] **Suggest** invoking `superpowers:brainstorming` skill (state the reason)
- [ ] Do NOT auto-invoke brainstorming
- [ ] Wait for the user's explicit nod before invoking

## Failure Signals

- Claude auto-invokes brainstorming without asking
- Claude silently absorbs the task and starts planning without offering brainstorming
- Claude asks the user to invoke brainstorming manually (code-mentor should do it, after the user nods)