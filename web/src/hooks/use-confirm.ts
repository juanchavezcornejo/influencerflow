"use client";

import { useCallback, useRef, useState } from "react";

interface ConfirmOptions {
  title: string;
  body?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "default" | "destructive";
}

interface ConfirmState extends ConfirmOptions {
  resolve: (value: boolean) => void;
}

export interface UseConfirmReturn {
  confirmState: ConfirmState | null;
  confirm: (options: ConfirmOptions) => Promise<boolean>;
  handleConfirm: () => void;
  handleCancel: () => void;
}

/**
 * Imperative confirm dialog hook.
 * Returns a `confirm(options) → Promise<boolean>` plus the state needed
 * to render <ConfirmDestructive> or any modal.
 *
 * Usage:
 *   const { confirm, confirmState, handleConfirm, handleCancel } = useConfirm();
 *   const ok = await confirm({ title: "Delete session?", variant: "destructive" });
 *
 * Wire `confirmState` into a <ConfirmDestructive> dialog; call
 * `handleConfirm` / `handleCancel` from its buttons.
 */
export function useConfirm(): UseConfirmReturn {
  const [confirmState, setConfirmState] = useState<ConfirmState | null>(null);
  const resolveRef = useRef<((value: boolean) => void) | null>(null);

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise<boolean>((resolve) => {
      resolveRef.current = resolve;
      setConfirmState({ ...options, resolve });
    });
  }, []);

  const handleConfirm = useCallback(() => {
    resolveRef.current?.(true);
    resolveRef.current = null;
    setConfirmState(null);
  }, []);

  const handleCancel = useCallback(() => {
    resolveRef.current?.(false);
    resolveRef.current = null;
    setConfirmState(null);
  }, []);

  return { confirmState, confirm, handleConfirm, handleCancel };
}
