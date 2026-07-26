# TC11 — Full Closing (Multi-File + API)

## Scenario

You are Claude with the `code-mentor` skill loaded. The user asked you to refactor an API call that spans 3 files; you have made all the changes. The user now says:

> 继续

## Verification Checklist

- [ ] Recognize this is a multi-file + API change → full closing
- [ ] Perform full closing:
  1. Recap oriented to skill growth (1–3 sentences): what did you learn, what to remember next time
  2. How to verify it works (commands or steps — e.g., run the test suite, hit the API endpoint)
  3. Interface / context: how this code fits in the project (which module owns it, what depends on it)
- [ ] After closing, ask "下一步做什么？"

## Failure Signals

- Claude uses light closing (under-reach)
- Claude skips the interface/context section
- Claude moves to the next task with no closing