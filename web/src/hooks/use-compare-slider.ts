"use client";

import { useCallback, useRef, useState } from "react";

export interface UseCompareSliderReturn {
  // Position as a percentage [0, 100].
  position: number;
  setPosition: (pct: number) => void;
  // Attach to the container div that wraps both images.
  containerRef: React.RefObject<HTMLDivElement | null>;
  // Attach to the drag handle element.
  handleProps: {
    onPointerDown: (e: React.PointerEvent) => void;
    onPointerMove: (e: React.PointerEvent) => void;
    onPointerUp: (e: React.PointerEvent) => void;
    role: "separator";
    "aria-label": string;
    "aria-valuenow": number;
    "aria-valuemin": number;
    "aria-valuemax": number;
  };
}

// Pointer-capture-based before/after slider position.
// Position persists across proposal cycles (pass it up via setPosition if needed).
export function useCompareSlider(initialPosition = 50): UseCompareSliderReturn {
  const [position, setPositionState] = useState(initialPosition);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const draggingRef = useRef(false);

  const clamp = (v: number) => Math.max(0, Math.min(100, v));

  const updateFromEvent = useCallback((e: React.PointerEvent) => {
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    setPositionState(clamp((x / rect.width) * 100));
  }, []);

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      draggingRef.current = true;
      e.currentTarget.setPointerCapture(e.pointerId);
      updateFromEvent(e);
    },
    [updateFromEvent],
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!draggingRef.current) return;
      updateFromEvent(e);
    },
    [updateFromEvent],
  );

  const onPointerUp = useCallback((e: React.PointerEvent) => {
    draggingRef.current = false;
    e.currentTarget.releasePointerCapture(e.pointerId);
  }, []);

  const setPosition = useCallback((pct: number) => setPositionState(clamp(pct)), []);

  return {
    position,
    setPosition,
    containerRef,
    handleProps: {
      onPointerDown,
      onPointerMove,
      onPointerUp,
      role: "separator",
      "aria-label": "Compare before and after",
      "aria-valuenow": Math.round(position),
      "aria-valuemin": 0,
      "aria-valuemax": 100,
    },
  };
}
