# TC4 — Patient Teacher Role

## Scenario

You are Claude with the `code-mentor` skill loaded (user has already entered mentor mode in this session). The user asks:

> 这个文件里的 useEffect 是干嘛的？

## Verification Checklist

- [ ] Switch to Patient teacher role (not Reliable pair-programmer)
- [ ] Give a concrete example, not just abstract description
- [ ] Annotate the term "useEffect" on first use (since the user is asking what it is)
- [ ] Do not write any code or suggest edits
- [ ] Do not trigger closing (this is a read-only explanation)

## Failure Signals

- Claude answers with abstract jargon without an example
- Claude assumes the user knows what useEffect is
- Claude writes example code without being asked
- Claude performs a closing when there was no edit