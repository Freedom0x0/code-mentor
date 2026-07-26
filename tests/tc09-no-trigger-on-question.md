# TC9 — No Trigger on Pure Question

## Scenario

You are Claude. The user opens a brand-new session and sends a single message:

> 这是啥？

## Verification Checklist

- [ ] Do NOT trigger `code-mentor` (no edit intent, no dev task)
- [ ] Answer normally as Claude (clarify what "啥" refers to, or give a generic explanation)
- [ ] Do NOT ask "要不要进入陪跑模式？" (no trigger condition met)
- [ ] Do NOT invoke any of the code-mentor workflow steps

## Failure Signals

- Claude triggers code-mentor and asks about mentor mode
- Claude asks the 3 clarifying questions
- Claude demands a specific file before answering