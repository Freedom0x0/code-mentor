# TC41 — Session Resume 读侧 · 「详细说说」展开

## Scenario

Continuation of TC40. Claude just reported the 1-sentence 「进度」 summary. User responds:

> 详细说说

## Verification Checklist (Claude must do all of these)

- [ ] Recognize 「详细说说」 as expand trigger
- [ ] Display remaining 3 fields: **未完成 / 关键文件 / 下次起手**
- [ ] 🔴 Do NOT extend to unrelated content (e.g., project history, codebase tour)
- [ ] 🔴 Do NOT modify the snapshot file
- [ ] 🔴 Do NOT auto-enter 4-step; wait for user指令

## Failure Signals (any of these = test fails)

- Claude expands only 1 or 2 fields (incomplete expansion)
- Claude auto-runs Clarify after expanding
- Claude reads from `session-snapshots/` historical files (user only asked about "上次" / the latest)
- Claude uses bullet points / markdown headers in ways that obscure file:line references