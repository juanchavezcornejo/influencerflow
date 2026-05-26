---
description: Show project state — containers, git, tasks
---

Print a compact snapshot of the project's current state. Do not re-scan
anything you've already checked this session.

1. **Dev stack:** `make ps` — show running services + health probes.
2. **Git:**
   - `git status --short` (uncommitted files)
   - `git log -1 --oneline` (last commit)
   - `git branch --show-current`
3. **Open tasks:** TaskList — active TaskCreate tasks, if any.
4. **Recent migrations:** list the 3 most recent files in
   `api/alembic/versions/` if it exists.

Keep each section to a handful of lines. No full diffs, no full logs.
