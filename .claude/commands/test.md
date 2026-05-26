---
description: Run all tests (api + web) and summarize failures
---

Run `make test`.

- If everything passes, report in one line: "All tests passed (N api + M web)."
- If something fails, show only the first failing assertion per test file,
  with `file:line` references. Don't paste the full traceback unless the
  user asks.
- If the user asked for a specific subset (e.g. "just api"), use
  `make test-api` or `make test-web` instead.
