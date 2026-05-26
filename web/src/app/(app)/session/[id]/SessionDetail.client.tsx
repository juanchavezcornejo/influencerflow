"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { apiFetch } from "@/lib/api-client";
import type { Session } from "@/types/api";
import { useSessionEvents } from "@/hooks/use-session-events";

const COPY = {
  syncing: "Syncing...",
  resync: "Resync",
  ready: "Ready",
  empty: "No assets yet",
  assets: "Assets",
};

interface Asset {
  id: string;
  thumbnail_url: string;
  original_filename: string;
  taken_at?: string;
}

export function SessionDetail({ sessionId }: { sessionId: string }) {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [assets, _setAssets] = useState<Asset[]>([]);
  const [progress, setProgress] = useState(0);
  const [syncing, setSyncing] = useState(false);

  // SSE hook for live progress
  const sseData = useSessionEvents(sessionId);

  useEffect(() => {
    const loadSession = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          router.push("/login");
          return;
        }

        const data = await apiFetch<Session>(`/sessions/${sessionId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSession(data);
        setSyncing(data.status === "syncing");

        // TODO: Load assets
      } catch (error) {
        console.error("Failed to load session:", error);
      }
    };

    loadSession();
  }, [sessionId, router]);

  // Update progress when SSE events arrive
  useEffect(() => {
    if (sseData?.type === "sync.progress") {
      setProgress(sseData.progress || 0);
    }
  }, [sseData]);

  if (!session) {
    return <div className="animate-pulse">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">{session.cloudFolderName}</h1>
        <Button variant="outline" onClick={() => router.refresh()}>
          {COPY.resync}
        </Button>
      </div>

      {syncing && (
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">{COPY.syncing}</p>
          <Progress value={progress} />
        </div>
      )}

      <div className="space-y-4">
        <h2 className="text-lg font-medium">{COPY.assets}</h2>
        {assets.length === 0 ? (
          <p className="text-muted-foreground">{COPY.empty}</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-2">
            {assets.map((asset) => (
              <div key={asset.id} className="aspect-square bg-secondary rounded-md overflow-hidden">
                <img
                  src={asset.thumbnail_url}
                  alt={asset.original_filename}
                  className="w-full h-full object-cover"
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
