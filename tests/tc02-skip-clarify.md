# TC2 — Skip Clarify

## Scenario

You are Claude with the `code-mentor` skill loaded. The user has already answered the 3 clarifying questions. After your restated "完成定义", the user says:

> 别问了直接干

## Verification Checklist

- [ ] Acknowledge the switch to no-confirmation mode (1 sentence)
- [ ] Do not ask any more clarifying questions for the rest of the session
- [ ] For the next file change, proceed without "confirm before edit" — but still announce in 1 sentence what is being done
- [ ] When the change is done, perform the closing (light or full per scenario)

## Failure Signals

- Claude continues asking for confirmation on every change after "直接干"
- Claude performs no closing at all
- Claude says "我直接干了" with no announcement of what changed