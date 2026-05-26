"use client";

import { useEffect, useState } from "react";

interface SSEEvent {
  type: string;
  progress?: number;
  current_file?: string;
  message?: string;
  [key: string]: unknown;
}

/**
 * Subscribe to Server-Sent Events for a session.
 * Receives sync progress updates in real-time.
 */
export function useSessionEvents(sessionId: string): SSEEvent | null {
  const [event, setEvent] = useState<SSEEvent | null>(null);

  // Read token once outside the effect body to avoid re-reading on every render.
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  useEffect(() => {
    if (!token || !sessionId) return;

    const eventSource = new EventSource(
      `/api/v1/events/session/${sessionId}?token=${token}`
    );

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as SSEEvent;
        setEvent(data);
      } catch (error) {
        console.error("Failed to parse SSE event:", error);
      }
    };

    eventSource.onerror = (e) => {
      console.error("SSE connection error:", e);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [sessionId, token]);

  return event;
}
