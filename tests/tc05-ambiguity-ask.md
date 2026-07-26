# TC5 — Ambiguity Asks Questions

## Scenario

You are Claude with the `code-mentor` skill loaded. The user says:

> 把那个用户登录的逻辑改了

## Verification Checklist

- [ ] Do NOT guess which login logic or which file
- [ ] Ask 2–3 clarifying questions such as:
  - 哪个文件 / 哪个函数？
  - 改成什么样（具体行为）？
  - 是否涉及 API / 数据库 / 前端组件？
- [ ] Do not start editing anything

## Failure Signals

- Claude picks a random file and starts editing
- Claude asks only one question when the requirements are unclear
- Claude asks "你想要什么" type open-ended questions instead of focused clarifying questions