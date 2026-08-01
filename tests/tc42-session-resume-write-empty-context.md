# TC42 — Session Resume 写侧 · 对话太短 / 没改东西

## Scenario

You are Claude with the `code-mentor` skill loaded. User just entered mentor mode (or had a very short session with no edits). User sends:

> 本次会话结束

## Verification Checklist (Claude must do all of these)

- [ ] Try to extract 4 fields from context
- [ ] Recognize context is too short / has no edits to extract from
- [ ] 🔴 Do NOT fabricate progress (e.g., "上次你做了 X" with no evidence)
- [ ] Ask user: "这次没改什么，要记一笔空快照吗？" (or equivalent)
- [ ] If user says no: skip silently, no file written
- [ ] If user says yes: write minimal snapshot with "进度：本次无改动" type placeholder

## Failure Signals (any of these = test fails)

- Claude writes a snapshot with fabricated progress
- Claude auto-saves an empty snapshot without asking
- Claude refuses to save at all (user might want a marker)
- Claude suggests user "改点东西再来收工" (gate-keeping, wrong response)