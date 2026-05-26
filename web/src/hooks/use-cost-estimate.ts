"use client";

import { useState, useCallback } from "react";
import { apiFetch } from "@/lib/api-client";
import type { CostEstimate } from "@/types/api";

export interface UseCostEstimateReturn {
  estimate: CostEstimate | null;
  loading: boolean;
  error: Error | null;
  fetch: (operation: string, inputs: Record<string, unknown>) => Promise<CostEstimate | null>;
  reset: () => void;
}

// Fetch a cost estimate before showing <CostConfirm>.
// Call fetch() when the user hovers or clicks the trigger — not on mount.
export function useCostEstimate(): UseCostEstimateReturn {
  const [estimate, setEstimate] = useState<CostEstimate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(
    async (operation: string, inputs: Record<string, unknown>) => {
      setLoading(true);
      setError(null);
      try {
        const result = await apiFetch<CostEstimate>("/cost/estimate", {
          method: "POST",
          body: { operation, inputs },
        });
        setEstimate(result);
        return result;
      } catch (err) {
        setError(err as Error);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const reset = useCallback(() => {
    setEstimate(null);
    setError(null);
  }, []);

  return { estimate, loading, error, fetch, reset };
}
