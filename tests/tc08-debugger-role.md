# TC8 — Debugger Role + Suggest Skill

## Scenario

You are Claude with the `code-mentor` skill loaded. The user is already in mentor mode and says:

> 这个接口反复报 500，我已经调了 3 轮还是不对

## Verification Checklist

- [ ] Switch to Rigor排查助手 role
- [ ] Hypothesize 2–3 likely causes (do not jump to a fix)
- [ ] Suggest `superpowers:systematic-debugging` skill if appropriate (state the reason)
- [ ] Do NOT auto-invoke systematic-debugging
- [ ] Do NOT immediately edit code without user's confirmation

## Failure Signals

- Claude edits code immediately without hypothesizing
- Claude auto-invokes systematic-debugging
- Claude gives only one cause hypothesis when multiple are plausible
- Claude skips the role switch and behaves as a generic pair-programmer