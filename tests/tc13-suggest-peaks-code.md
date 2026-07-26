# TC13 — Suggest Peaks-Code for Big Scope

## Scenario

You are Claude with the `code-mentor` skill loaded. The user says:

> 老板让我做新需求 X，涉及 5 个模块，要走完整开发

## Verification Checklist

- [ ] Recognize this exceeds mentor mode's intended scope (multi-module full development)
- [ ] **Suggest** invoking `peaks-code` (state the reason: "需要走完整开发流水线")
- [ ] Do NOT auto-invoke peaks-code
- [ ] Do NOT try to fit this entire task into mentor mode
- [ ] Wait for the user's decision

## Failure Signals

- Claude tries to handle a 5-module task inside mentor mode
- Claude auto-invokes peaks-code
- Claude silently absorbs the task and starts clarifying as if it were a small task