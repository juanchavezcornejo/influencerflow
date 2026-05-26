---
description: Load a single screen spec from DESIGN.md (layout, data, states)
argument-hint: "screen slug, e.g. /session/{id} or dashboard"
---

Look up one screen in `docs/DESIGN.md`.

Expected argument: the route or a short slug, e.g.:
- `/login` or `login`
- `/dashboard` or `dashboard`
- `/dashboard/new` or `new-session`
- `/session/{id}` or `session` or `review`
- `/edit/{assetId}` or `edit`
- `/session/{id}/cost` or `cost`
- `/settings` or `settings`

If no argument is given, print the list above and stop.

Steps:
1. Map the argument to the §6.x section in `docs/DESIGN.md`:
   - login → §6.1
   - dashboard → §6.2
   - new-session / dashboard/new → §6.3
   - session / review / /session/{id} → §6.4
   - edit / /edit/{assetId} → §6.5
   - cost → §6.6
   - settings → §6.7
2. Read that section in full.
3. Report:
   - **Route** + **Purpose** (one sentence).
   - **Layout** bullet list.
   - **Data required** (the TypeScript shapes from the section).
   - **States** (idle / loading / empty / error / ready + any domain-specific ones).
   - **Responsive notes**.
   - **Keyboard shortcuts / interactions**.
   - **Related tickets** from `docs/MVP_SPEC.md` (the W#-### numbers listed at the header of the section).
4. Remind the user that every UI change must pass the checklist in
   DESIGN.md §11.

Do not start writing code — this command is for loading context, not
implementation. When the user asks you to implement something, `/ticket
<code>` is the right entry point.
