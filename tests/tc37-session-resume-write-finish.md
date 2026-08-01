# TC37 — Session Resume 写侧 · 「收工」同义口令

## Scenario

You are Claude with the `code-mentor` skill loaded. User is already in mentor mode. User sends:

> 收工

## Verification Checklist (Claude must do all of these)

- [ ] Recognize 「收工」as Session Resume write-side trigger (synonym of 「本次会话结束」)
- [ ] Same behavior as TC36: extract 4 fields → show draft → ASK confirm → write on confirm
- [ ] 🔴 Do NOT write any file before user confirms

## Failure Signals (any of these = test fails)

- Claude treats 「收工」 as ambiguous and asks "什么收工？"
- Claude writes the file without showing draft
- Claude silently treats 「收工」 as a normal closing signal (run light/full closing instead)