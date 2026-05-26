#!/usr/bin/env bash
# Wipe the local ./data volume (previews, originals, edits, exports).
# Mirrors what Resync does server-side. Destructive — prompts for confirmation.
source "$(dirname "$0")/_lib.sh"

targets=("data" "api/data")

printf "%sThis will delete:%s\n" "$C_BOLD" "$C_RESET"
for t in "${targets[@]}"; do
  [[ -e "$t" ]] && printf "  - %s (%s)\n" "$t" "$(du -sh "$t" 2>/dev/null | cut -f1)"
done

read -r -p "Continue? [y/N] " reply
[[ "$reply" =~ ^[Yy]$ ]] || die "Aborted"

for t in "${targets[@]}"; do
  if [[ -e "$t" ]]; then
    rm -rf "$t"
    ok "Removed $t"
  fi
done
