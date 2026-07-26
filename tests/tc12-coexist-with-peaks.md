# TC12 — Coexist With Peaks-Code

## Scenario

You are Claude. The user has just invoked `/peaks-code` and is in the middle of the peaks pipeline. They send a message:

> 帮我看下这个文件怎么改

## Verification Checklist

- [ ] Recognize that peaks-code is already orchestrating; do NOT take over with code-mentor
- [ ] Respond as a normal Claude within the peaks pipeline context (read the file, give advice)
- [ ] Do NOT ask "要不要进入陪跑模式？" (already in a workflow)
- [ ] Do NOT invoke any of the 4-step mentor workflow

## Failure Signals

- Claude triggers code-mentor and starts asking clarifying questions
- Claude silently drops the user's request
- Claude suggests switching to code-mentor when peaks-code is already running