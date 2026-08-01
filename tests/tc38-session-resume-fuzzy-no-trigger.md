# TC38 — Session Resume 模糊词不触发

## Scenario

You are Claude with the `code-mentor` skill loaded. User is already in mentor mode. User sends:

> 先休息一下

(or: 「我先关电脑」)

## Verification Checklist (Claude must do all of these)

- [ ] Recognize this is NOT a Session Resume write-side trigger (模糊词)
- [ ] 🔴 Do NOT auto-write any snapshot
- [ ] Continue normal mentor mode flow (4-step rhythm, current task, etc.)
- [ ] Do NOT ask "确认保存吗？" (would be forcing a write)

## Failure Signals (any of these = test fails)

- Claude treats 「先休息一下」 as 「本次会话结束」 and tries to write a snapshot
- Claude asks user "这是收工吗？" (false-positive questioning)
- Claude pre-emptively writes a draft snapshot to be safe