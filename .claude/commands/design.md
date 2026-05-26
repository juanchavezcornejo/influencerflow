---
description: Show the DESIGN.md index — screens, tokens, checklists
---

Print a compact map of `docs/DESIGN.md` so the user (or you) can jump straight to the relevant section without re-reading the whole file.

```
§1   Principles            — calm surface, always show state, paid = explicit, keyboard-first
§2   Visual system         — HSL tokens, typography scale, spacing, radii, elevation, motion
§3   Responsive            — breakpoints, grid templates, nav patterns, touch targets
§4   Accessibility         — focus, contrast, alt text, live regions, modals
§5   Layout primitives     — AppShell, Sidebar, TopBar, EmptyState, CostBadge, CostConfirm
§6.1 /login
§6.2 /dashboard            — sessions list + Drive status
§6.3 /dashboard/new        — folder picker
§6.4 /session/{id}         — review grid + groups
§6.5 /edit/{assetId}       — slider + correction tabs (color, crop, remove, face)
§6.6 /session/{id}/cost    — cost breakdown
§6.7 /settings             — language, budget, integrations, style seed
§6.8 Modals                — CostConfirm, ConfirmDestructive, ConnectDrive, FaceCrop, ExportReady
§6.9 Empty & error copy    — Spanish catalog
§7   Loading-state playbook
§8   Cost UX pattern       — mandatory for paid ops
§9   Copy & tone           — Spanish default, numbers, dates
§10  File placement        — src/ layout
§11  PR checklist          — the list every UI change must pass
§12  Open questions
```

Before editing anything under `web/`, read the DESIGN.md section for the
screen you're touching **and** the checklist in §11. Pair this with
`docs/FRONTEND.md` (conventions) — DESIGN = what it looks like, FRONTEND =
how to build it.
