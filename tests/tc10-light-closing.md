# TC10 — Light Closing (Small Change)

## Scenario

You are Claude with the `code-mentor` skill loaded. The user asked you to fix a typo in one file; you made the edit. The user now says:

> 继续

## Verification Checklist

- [ ] Recognize this is a 1-file / ≤ 20-line change → light closing
- [ ] Perform light closing only:
  - One-sentence recap of what was done
  - How to verify (e.g., "打开文件确认 typo 已修复" or a quick visual diff)
- [ ] Do NOT perform full closing (no interface/context section)
- [ ] After closing, ask "下一步做什么？"

## Failure Signals

- Claude performs full closing (over-reach)
- Claude skips closing entirely
- Claude launches into the next change with no closing