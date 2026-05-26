import { apiFetch } from "@/lib/api-client";
import type { Settings } from "@/types/api";
import SettingsForm from "./SettingsForm.client";

export const metadata = { title: "Settings — InfluencerFlow" };

export default async function SettingsPage() {
  const settings = await apiFetch<Settings>("/settings");

  return (
    <main className="container py-8">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Configure API keys, budget caps, and caption style.
        </p>
      </header>
      <SettingsForm initial={settings} />
    </main>
  );
}
