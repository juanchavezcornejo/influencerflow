#!/usr/bin/env bash
# Pre-tool-use hook: enforce DESIGN.md compliance for web/src/ edits.
# Fires before every Write and Edit tool call.
# Exits 0 (advisory only — never blocks). Output is injected into Claude's context.

set -euo pipefail

INPUT=$(cat)

# Extract file_path from tool input JSON (works for both Write and Edit tools)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    tip = d.get('tool_input', d)  # some versions wrap, some don't
    print(tip.get('file_path', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

# Only act on web/src/ files
if ! echo "$FILE_PATH" | grep -q "web/src/"; then
  exit 0
fi

cat <<'REMINDER'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 UI FILE — DESIGN COMPLIANCE CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before writing this file, confirm you have:

1. READ  docs/DESIGN.md — screen spec for the route you're touching
         (/screen <slug> loads the section quickly)
2. READ  docs/FRONTEND.md — Next.js/TS/Tailwind/shadcn conventions
3. SKILL ui-changes is active for this task

DESIGN.md §11 PR CHECKLIST (must pass):
  □ Tailwind tokens only — bg-background, text-foreground, border-border
    No hsl(), no hex, no raw Tailwind color names (blue-500, etc.)
  □ Responsive baseline xl → degrades cleanly to sm
  □ Dark theme default — no hardcoded light-mode colors
  □ Every interactive element keyboard-reachable with a visible focus ring
    (never remove focus-visible:ring-2)
  □ All <img> / <Image> have meaningful alt text
  □ Every async op has loading + success + error states (DESIGN.md §7)
  □ Paid ops: <CostBadge> on trigger + <CostConfirm> before running (§5.7–5.8, §8)
  □ Destructive ops: <ConfirmDestructive> or inline confirm
  □ User-facing strings grouped at top of file (pre-next-intl)
  □ No default export unless Next.js page.tsx / layout.tsx
  □ Types imported from @/types/api — no inline re-declarations

STOP AND RAISE if you are about to:
  • Introduce a new top-level color not in the §2.1 token table
  • Add a drop shadow outside a modal/popover
  • Invent a new modal shape when CostConfirm/ConfirmDestructive fit
  • Write a custom form control that shadcn already provides
  • Disable the focus ring
  • Change the font-weight scale

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REMINDER

exit 0
