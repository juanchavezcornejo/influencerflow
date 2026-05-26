import { cookies } from "next/headers";
import { apiFetch } from "@/lib/api-client";
import type { Settings } from "@/types/api";
import SettingsForm from "./SettingsForm.client";

export const metadata = { title: "Settings — InfluencerFlow" };

export default async function SettingsPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value ?? null;

  let settings: Settings | null = null;
  if (token) {
    try {
      settings = await apiFetch<Settings>("/settings", {
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      // Will fall through to form with defaults
    }
  }

  return (
    <main className="container py-8">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Configure API keys, budget caps, and caption style.
        </p>
      </header>
      <SettingsForm initial={settings ?? {
        claudeApiKey: null,
        replicateApiKey: null,
        googleClientId: null,
        googleClientSecret: null,
        sessionBudgetUsd: 10.0,
        sessionHardCapUsd: 50.0,
        styleSeed: null,
      }} />
    </main>
  );
}
