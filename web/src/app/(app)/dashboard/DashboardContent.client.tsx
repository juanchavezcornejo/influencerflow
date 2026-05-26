"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { Session } from "@/types/api";

const COPY = {
  newSession: "New session",
  connectDrive: "Connect Google Drive",
  noSessions: "No sessions yet",
  createOne: "Create one to get started",
};

interface DashboardContentProps {
  initialSessions: Session[];
}

export function DashboardContent({ initialSessions }: DashboardContentProps) {
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-medium">Your sessions</h2>
        <div className="flex items-center gap-3">
          <Link
            href="/settings"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Settings
          </Link>
          <Button onClick={() => router.push("/dashboard/new")}>
            {COPY.newSession}
          </Button>
        </div>
      </div>

      {initialSessions.length === 0 ? (
        <Card className="p-8 text-center space-y-4">
          <p className="text-muted-foreground">{COPY.noSessions}</p>
          <p className="text-sm text-muted-foreground">{COPY.createOne}</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {initialSessions.map((session) => (
            <Card
              key={session.id}
              className="p-4 cursor-pointer hover:border-ring"
              onClick={() => router.push(`/session/${session.id}`)}
            >
              <h3 className="font-medium truncate">{session.cloudFolderName}</h3>
              <p className="text-xs text-muted-foreground">
                {new Date(session.createdAt).toLocaleDateString()}
              </p>
              <div className="mt-2">
                <span className="text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded-full">
                  {session.status}
                </span>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
