---
description: Auto-format and auto-fix (ruff format, ruff --fix, prettier)
---

Run `make format`.

Report which files changed (one line per file, grouped by api/ vs web/).
If nothing changed, say "Already formatted."

After formatting, if the user is mid-task, continue with their original
request. Do not re-run lint unless asked.
