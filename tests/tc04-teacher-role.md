# TC4 — Patient Teacher Role vs. Post-edit Teach-back

## Scenario

You are Claude with the `code-mentor` skill loaded (user has already entered mentor mode in this session). The user asks:

> 这个文件里的 useEffect 是干嘛的？

## Verification Checklist

- [ ] Switch to Patient teacher role (not Reliable pair-programmer)
- [ ] Give a concrete example, not just abstract description
- [ ] Annotate the term "useEffect" on first use (since the user is asking what it is)
- [ ] Do not write any code or suggest edits
- [ ] Do not trigger closing (this is a read-only explanation)
- [ ] Do **not** do a post-edit teach-back (no edit was made — teach-back only follows actual code changes)

## Role vs. Teach-back Distinction

| | Patient teacher role | Post-edit teach-back |
|---|---|---|
| Trigger | User asks an explanation question ("这是啥"、"怎么理解") | After every code edit, before closing |
| Purpose | Explain a concept the user doesn't know | Walk the user through what just changed and why |
| Code change? | No | Yes (just happened) |

## Failure Signals

- Claude answers with abstract jargon without an example
- Claude assumes the user knows what useEffect is
- Claude writes example code without being asked
- Claude performs a closing when there was no edit
- Claude does a teach-back when no edit was made (confusing teacher role with teach-back)
