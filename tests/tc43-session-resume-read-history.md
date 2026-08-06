# TC43 — Session Resume 读侧 · 「上次上次呢」查历史

## Scenario

User in mentor mode has already done TC40 (read latest snapshot). User now asks:

> 上次上次呢

## Verification Checklist (Claude must do all of these)

- [ ] Recognize this is a request to read historical snapshots, not the latest
- [ ] List `session-snapshots/` directory sorted by mtime (newest first)
- [ ] 🔴 Do NOT modify any historical snapshot (read-only)
- [ ] Let user pick which session to view
- [ ] 🔴 Do NOT auto-read the most recent historical snapshot

## Failure Signals (any of these = test fails)

- Claude reads the latest snapshot again (already showed in TC40)
- Claude auto-picks the most recent historical snapshot
- Claude modifies / deletes historical snapshots
- Claude silently combines latest + historical into one report