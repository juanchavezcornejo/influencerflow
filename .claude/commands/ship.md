---
description: Pre-PR checklist — lint + test + typecheck + diff summary
---

Pre-PR sanity check before the user opens a pull request.

Run, in order:
1. `make lint` — stop if fails. Report exactly what's broken.
2. `make test` — stop if fails. Report first failing test per file.
3. `git status` + `git diff --stat` — summarize what's changing:
   - Files touched (grouped by `api/` vs `web/` vs `docs/` vs other).
   - Net lines added/removed.
   - Any new migrations in `api/alembic/versions/`? Flag them — PR description
     should mention the migration.
   - Any untracked files that look important (missed `git add`)?
4. Suggest a Conventional Commit message based on the diff shape:
   - New capability → `feat: ...`
   - Fixing something broken → `fix: ...`
   - Refactor with no behavior change → `refactor: ...`
   - Tests / docs / chore as applicable.

Do NOT commit, push, or open a PR — the user drives that. Just report.
