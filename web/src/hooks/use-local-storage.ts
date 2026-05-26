"use client";

import { useCallback, useState } from "react";

// Typed localStorage hook. SSR-safe: falls back to initialValue on the server.
// Usage: const [sidebarOpen, setSidebarOpen] = useLocalStorage("sidebar-open", true)
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
): readonly [T, (next: T | ((prev: T) => T)) => void] {
  const [value, setValue] = useState<T>(() => {
    if (typeof window === "undefined") return initialValue;
    try {
      const raw = window.localStorage.getItem(key);
      return raw !== null ? (JSON.parse(raw) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const set = useCallback(
    (next: T | ((prev: T) => T)) => {
      setValue((prev) => {
        const resolved = typeof next === "function" ? (next as (p: T) => T)(prev) : next;
        try {
          window.localStorage.setItem(key, JSON.stringify(resolved));
        } catch {
          // quota exceeded — continue in-memory
        }
        return resolved;
      });
    },
    [key],
  );

  return [value, set] as const;
}
