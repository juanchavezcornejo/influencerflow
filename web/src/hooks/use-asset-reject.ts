"use client";

import { useCallback, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import type { AssetStatus } from "@/types/api";

interface UseAssetRejectOptions {
  onSettled?: (assetId: string, status: AssetStatus) => void;
}

// Optimistically toggle an asset's rejected/active status.
// Rolls back on API failure and calls onSettled in both cases.
export function useAssetReject({ onSettled }: UseAssetRejectOptions = {}) {
  const [pending, setPending] = useState<Set<string>>(new Set());

  const toggle = useCallback(
    async (assetId: string, currentStatus: AssetStatus) => {
      if (pending.has(assetId)) return;
      const nextStatus: AssetStatus = currentStatus === "rejected" ? "active" : "rejected";

      setPending((prev) => new Set(prev).add(assetId));
      // Optimistic update: caller should treat this assetId + nextStatus as the new state.
      onSettled?.(assetId, nextStatus);

      try {
        await apiFetch<void>(`/assets/${assetId}/status`, {
          method: "PATCH",
          body: { status: nextStatus },
        });
      } catch {
        // Roll back
        onSettled?.(assetId, currentStatus);
      } finally {
        setPending((prev) => {
          const next = new Set(prev);
          next.delete(assetId);
          return next;
        });
      }
    },
    [pending, onSettled],
  );

  return { toggle, isPending: (id: string) => pending.has(id) };
}
