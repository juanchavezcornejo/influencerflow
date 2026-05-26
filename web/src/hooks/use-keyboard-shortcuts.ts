"use client";

import { useEffect, useRef } from "react";

type Handler = (e: KeyboardEvent) => void;

// Map of key string → handler. Key format: "A", "ArrowLeft", "Shift+R", "Meta+K".
type ShortcutMap = Record<string, Handler>;

// Bind keyboard shortcuts globally. Skips when focus is inside an input or
// contenteditable element so typing doesn't trigger shortcuts.
//
// Usage:
//   useKeyboardShortcuts({ ArrowLeft: () => prev(), Enter: () => accept() }, isActive)
export function useKeyboardShortcuts(shortcuts: ShortcutMap, active = true): void {
  // Keep a stable ref so the effect doesn't re-run when the map object changes identity.
  const shortcutsRef = useRef<ShortcutMap>(shortcuts);
  shortcutsRef.current = shortcuts;

  useEffect(() => {
    if (!active) return;

    const handler = (e: KeyboardEvent): void => {
      const target = e.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        return;
      }

      const parts: string[] = [];
      if (e.metaKey) parts.push("Meta");
      if (e.ctrlKey) parts.push("Ctrl");
      if (e.shiftKey) parts.push("Shift");
      if (e.altKey) parts.push("Alt");
      parts.push(e.key);
      const key = parts.join("+");

      const fn = shortcutsRef.current[key];
      if (fn) {
        e.preventDefault();
        fn(e);
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [active]);
}
