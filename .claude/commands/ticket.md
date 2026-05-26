---
description: Start work on an MVP_SPEC ticket (loads it, proposes branch + breakdown)
argument-hint: "ticket code, e.g. W1-005"
---

Start work on a ticket from `docs/MVP_SPEC.md`.

Expected argument: a ticket code like `W1-005` or `TCKT-W1-005` (strip the
`TCKT-` prefix if present). If no argument is given, ask for one.

Steps:
1. Grep `docs/MVP_SPEC.md` for `TCKT-<CODE>` and read the full ticket block
   (title, scope, estimate, depends on, acceptance criteria).
2. Check the `Depends on` field. If any dependency is not yet implemented
   (scan the repo briefly for the marker files/tables/routes), flag it
   before starting.
3. Propose a branch name: `w{N}-{slug-from-title}` (lowercase,
   kebab-case, no `tckt-` prefix). Example: `W1-005` → `w1-gdrive-oauth`.
4. Propose a task breakdown using TaskCreate — one task per acceptance
   criterion, in the order they'll be implemented.
5. Propose the first file(s) to create or change. Do not start writing
   code until the user confirms.

Do NOT create a git branch or commit anything — the user drives that.
