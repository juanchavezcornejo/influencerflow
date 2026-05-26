---
description: Run lint + typecheck + format check, offer to auto-format if dirty
---

Run `make lint`.

If clean: one-line confirmation.

If not clean:
1. Show a concise breakdown: which tool, how many violations, file:line for
   the first few.
2. If every violation is auto-fixable (ruff format, prettier, ruff --fix),
   propose running `/format` and ask for confirmation.
3. If some are not auto-fixable (e.g. mypy errors, real eslint bugs), list
   only those and stop — they need thought, not a re-run.
