---
name: ui-changes
description: |
  Guardrails and workflow for any change under `web/` — pages, components,
  hooks, styles, layout. Activates when the user asks to add, edit, or
  review anything UI-facing, or when you're about to write to a file under
  `web/src/`. Ensures every change conforms to `docs/DESIGN.md` (visual +
  UX spec) and `docs/FRONTEND.md` (conventions).
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---

# ui-changes

Use this skill whenever the current task touches the frontend — a new
page, a new component, a visual tweak, a new hook, a responsive fix, a
copy change, anything under `web/`.

## When to activate

- User says "add a page / screen / component / modal / hook / panel".
- User says "make this responsive / a11y / dark-mode / mobile / tablet".
- User references a route (`/session/{id}`, `/edit/…`, `/dashboard`, …).
- A tool call is about to Write or Edit a file whose path contains
  `web/src/`.
- User asks to review or audit existing UI.

## Canonical sources (read these first, in this order)

1. `docs/DESIGN.md` — screens, tokens, responsive grid templates, cost
   UX, state playbook, copy tone, checklist.
2. `docs/FRONTEND.md` — Next.js/TS/Tailwind/shadcn conventions, path
   aliases, `apiFetch`, SSE hook contract.
3. `docs/MVP_SPEC.md` — acceptance criteria for the ticket you're on, if
   any (run `/ticket <code>` to load it).

Treat these as the source of truth. If the current file diverges from
them, raise that with the user before propagating the divergence.

## Workflow for a UI change

1. **Locate the screen in DESIGN.md.**
   - `/screen <slug>` (slash command) prints the section you need, or
     read §6.x directly.
   - Note the **data shapes**, **states**, **responsive notes**, and
     **shortcuts** listed for that screen.
2. **Identify the component(s) you'll add or edit.**
   - If reusable cross-feature → `components/shared/`.
   - Review-grid-specific → `components/review/`.
   - Edit-view-specific → `components/edit/`.
   - Strictly one-page-only → `app/.../_components/`.
3. **Check if a primitive already exists** in `components/ui/` (shadcn)
   or `components/shared/`. Don't re-roll. If shadcn has it,
   `pnpm dlx shadcn@latest add <name>` — never hand-write.
4. **Types live in `web/src/types/api.ts`.** Extend there; don't redeclare
   the same `Session` / `Asset` / etc. inline.
5. **Data fetching** goes through `apiFetch<T>()` in server components
   by default; interactive bits in sibling `*.client.tsx`. See
   `FRONTEND.md`.
6. **Apply the DESIGN.md PR checklist** (§11) before declaring done.

## PR checklist (inline — keep in sync with DESIGN.md §11)

- [ ] Uses Tailwind tokens (`bg-background`, `text-foreground`, …), not
      hand-mixed `hsl(...)` or custom hex.
- [ ] Responsive baseline at `xl`, degrades to `sm` without breaking.
- [ ] Works in the dark theme (`.dark` on `<html>` is default).
- [ ] Every interactive element is keyboard-reachable with a visible
      focus ring.
- [ ] All images have meaningful `alt`.
- [ ] Async flows show loading + success + error (see DESIGN.md §7).
- [ ] Paid ops use `<CostBadge>` on the trigger and `<CostConfirm>`
      before running (DESIGN.md §5.7–5.8, §8).
- [ ] Destructive ops confirm via `<ConfirmDestructive>` (or inline for
      small cases).
- [ ] User-facing strings grouped at the top of the component file
      (pre-`next-intl`).
- [ ] No default export unless it's a Next.js `page.tsx` / `layout.tsx`.
- [ ] Types come from `@/types/api`; no duplicated shape declarations.

## Responsive templates (copy-paste from DESIGN.md §3.2)

- Dense (asset grid):
  `grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-2`
- Comfortable (session cards):
  `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`
- Form: `grid-cols-1 md:grid-cols-2 gap-4`

## Things that should make you stop and confirm

- **Adding a new top-level color.** The token palette is exhaustive
  (§2.1). If you think you need a new color, you probably need to reuse
  one of the semantic chips.
- **Adding a drop shadow** outside of modals/popovers.
- **Inventing a new modal shape** when `<CostConfirm>` /
  `<ConfirmDestructive>` already match the intent.
- **Writing a custom form control** when shadcn has one.
- **Disabling the focus ring.**
- **Changing default font / font-weight scale.**

If you catch yourself doing any of the above, pause and raise it to the
user with a one-line justification — don't ship it silently.

## After you finish

- Run `make lint` (or `/lint`). If it's dirty, `/format`.
- If you touched types, run `pnpm typecheck` in `web/`.
- When tests exist (W6+), run `pnpm test`.
- Write or update no docs unless DESIGN.md diverges — in that case,
  amend DESIGN.md in the same change and note it in
  `docs/DECISIONS.md`.
