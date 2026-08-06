# TC40 — Session Resume 读侧 · 有快照 · 1 句话摘要

## Scenario

You are Claude with the `code-mentor` skill loaded. User opens session and sends:

> 继续工作

The project has a `session-snapshot.md` with 4 fields populated.

## Verification Checklist (Claude must do all of these)

- [ ] Recognize 「继续工作」as read trigger
- [ ] Read `session-snapshot.md`
- [ ] Report **only the 「进度」field** as a one-sentence summary
- [ ] 🔴 Do NOT expand the other 3 fields (未完成 / 关键文件 / 下次起手) without user asking
- [ ] 🔴 Do NOT auto-enter 4-step Clarify (user said "等具体指令才进")

## Failure Signals (any of these = test fails)

- Claude reads and dumps all 4 fields immediately
- Claude auto-runs Clarify questions after reading snapshot
- Claude paraphrases or rewrites the 「进度」field instead of quoting/paraphrasing faithfully
- Claude modifies the snapshot file (read-only operation)