---
description: Remove build/install caches (keeps ./data)
---

`make clean` removes `.venv`, `node_modules`, `.next`, `.pytest_cache`,
`.mypy_cache`, `.ruff_cache`, `__pycache__`, and web cache dirs. It does
**not** touch `./data` (use `/clean-data` or `make clean-data` for that).

Before running:
1. Confirm with the user — this will force a re-install on next `make dev`.
2. Make sure the dev stack is stopped (`make ps`). If it's up, warn that
   stopping it is recommended first.

Then run `make clean` and report what was removed.
