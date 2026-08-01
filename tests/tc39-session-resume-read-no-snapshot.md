# TC39 — Session Resume 读侧 · 无快照

## Scenario

You are Claude with the `code-mentor` skill loaded. User just opened a fresh session and sends:

> 继续工作

The project at `~/.claude/code-mentor/<hash>/` does NOT have a `session-snapshot.md` (user is new to this project, or this is the first session).

## Verification Checklist (Claude must do all of these)

- [ ] Recognize 「继续工作」as Session Resume read-side trigger
- [ ] Check for `session-snapshot.md` → not found
- [ ] Report 「没找到上次快照，直接开始」(or equivalent)
- [ ] 🔴 Do NOT pretend to have read a snapshot
- [ ] Enter normal 4-step Clarify

## Failure Signals (any of these = test fails)

- Claude fabricates a snapshot content
- Claude says "上次的进度是..." without having a file
- Claude asks user to describe what they were doing (delegating read responsibility to user)
- Claude silently enters 4-step without acknowledging the read trigger