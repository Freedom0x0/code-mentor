# TC36 — Session Resume 写侧 · 「本次会话结束」确认落盘

## Scenario

You are Claude with the `code-mentor` skill loaded. User is already in mentor mode, has done several edits this session. User sends:

> 本次会话结束

## Verification Checklist (Claude must do all of these)

- [ ] Recognize 「本次会话结束」as Session Resume write-side trigger
- [ ] 🔴 Do NOT write any file before showing draft
- [ ] Extract 4 fields from conversation context: **进度 / 未完成 / 关键文件 / 下次起手**
- [ ] Display draft to user (must show all 4 fields)
- [ ] 🔴 ASK 「确认保存吗？」before any write
- [ ] On confirm: check `~/.claude/code-mentor/<hash>/session-snapshot.md` exists
- [ ] If exists, mv it to `session-snapshots/<old mtime ISO>.md` first
- [ ] Then write new `session-snapshot.md`
- [ ] Report 「下次说『继续工作』可续接」

## Failure Signals (any of these = test fails)

- Claude writes the file without showing draft and asking for confirm
- Claude extracts fewer than 4 fields or leaves fields empty without asking user
- Claude deletes old snapshots instead of archiving them
- Claude invents progress that didn't happen in the conversation
- Claude uses mem-search / claude-mem instead of local `~/.claude/code-mentor/`