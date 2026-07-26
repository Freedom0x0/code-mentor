# TC3 — Closing Before Continue

## Scenario

You are Claude with the `code-mentor` skill loaded. The user asked you to change a file; you have made the edit. The user now says:

> 继续

## Verification Checklist

- [ ] Do NOT immediately start the next change
- [ ] Perform closing (light or full per the scope rules in SKILL.md):
  - Light: one-sentence recap + how to verify
  - Full: recap + verification + interface/context
- [ ] After closing, ask "下一步做什么？"

## Failure Signals

- Claude starts editing the next file with no closing
- Claude performs only a partial closing (e.g., recap without verification)
- Claude performs full closing on a 5-line typo (over-reach; should be light)