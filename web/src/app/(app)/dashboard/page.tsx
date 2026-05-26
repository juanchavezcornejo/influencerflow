import { redirect } from "next/navigation";
import { apiFetch } from "@/lib/api-client";
import type { Session } from "@/types/api";
import { DashboardContent } from "./DashboardContent.client";

export const metadata = {
  title: "Dashboard — InfluencerFlow",
};

async function getSessions(token: string | null) {
  if (!token) return [];
  try {
    return await apiFetch<Session[]>("/sessions", {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    return [];
  }
}

export default async function DashboardPage() {
  // Get token from request headers (set by middleware)
  const token = null; // TODO: extract from cookies via getServerSession or similar

  if (!token) {
    redirect("/login");
  }

  const sessions = await getSessions(token);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Sessions</h1>
      <DashboardContent initialSessions={sessions} />
    </div>
  );
}
