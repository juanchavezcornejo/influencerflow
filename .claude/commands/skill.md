---
description: List available docs and when to consult each
---

Print the project's doc index as a reference the user (or you) can use to
find information without grepping.

```
docs/ARCHITECTURE.md — detailed backend design (schema, data model, deploy)
docs/MVP_SPEC.md     — 6-week ticket-by-ticket build plan
docs/BACKEND.md      — FastAPI / SQLAlchemy / Celery conventions
docs/FRONTEND.md     — Next.js App Router conventions
docs/DEVOPS.md       — docker-compose + Railway + secrets
docs/TESTING.md      — pytest, eager Celery, Playwright plan
docs/COMMANDS.md     — every script / make target / slash command
docs/DECISIONS.md    — append-only ADR log
docs/PROMPTS.md      — Claude prompt library (for AI features)
CLAUDE.md            — product-level intent + principles
```

Before grepping the codebase for "where does X live" or "how do I run Y",
check the relevant doc first.
