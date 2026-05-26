"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api-client";
import { useToast } from "@/hooks/use-toast";
import type { Settings, SettingsPatch } from "@/types/api";

interface Props {
  initial: Settings;
}

export default function SettingsForm({ initial }: Props) {
  const router = useRouter();
  const { addToast } = useToast();

  const [claudeKey, setClaudeKey] = useState("");
  const [replicateKey, setReplicateKey] = useState("");
  const [googleClientId, setGoogleClientId] = useState(initial.googleClientId ?? "");
  const [googleClientSecret, setGoogleClientSecret] = useState("");
  const [budgetUsd, setBudgetUsd] = useState(String(initial.sessionBudgetUsd));
  const [hardCapUsd, setHardCapUsd] = useState(String(initial.sessionHardCapUsd));
  const [styleSeed, setStyleSeed] = useState(initial.styleSeed ?? "");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);

    const patch: SettingsPatch = {};
    if (claudeKey) patch.claudeApiKey = claudeKey;
    if (replicateKey) patch.replicateApiKey = replicateKey;
    if (googleClientId !== (initial.googleClientId ?? "")) patch.googleClientId = googleClientId;
    if (googleClientSecret) patch.googleClientSecret = googleClientSecret;
    const budget = parseFloat(budgetUsd);
    if (!isNaN(budget) && budget !== initial.sessionBudgetUsd) patch.sessionBudgetUsd = budget;
    const hardCap = parseFloat(hardCapUsd);
    if (!isNaN(hardCap) && hardCap !== initial.sessionHardCapUsd) patch.sessionHardCapUsd = hardCap;
    if (styleSeed !== (initial.styleSeed ?? "")) patch.styleSeed = styleSeed;

    try {
      await apiFetch<Settings>("/settings", { method: "PATCH", body: patch as Record<string, unknown> });
      addToast("Settings saved", "success");
      router.refresh();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save settings";
      addToast(message, "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8 max-w-lg">
      {/* Integrations */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Integrations
        </h2>

        <div className="space-y-2">
          <Label htmlFor="claudeKey">Claude API Key</Label>
          <Input
            id="claudeKey"
            type="password"
            placeholder={initial.claudeApiKey ?? "sk-ant-..."}
            value={claudeKey}
            onChange={(e) => setClaudeKey(e.target.value)}
            autoComplete="off"
          />
          <p className="text-xs text-muted-foreground">Leave blank to keep current key.</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="replicateKey">Replicate API Token</Label>
          <Input
            id="replicateKey"
            type="password"
            placeholder={initial.replicateApiKey ?? "r8_..."}
            value={replicateKey}
            onChange={(e) => setReplicateKey(e.target.value)}
            autoComplete="off"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="googleClientId">Google OAuth Client ID</Label>
          <Input
            id="googleClientId"
            type="text"
            value={googleClientId}
            onChange={(e) => setGoogleClientId(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="googleClientSecret">Google OAuth Client Secret</Label>
          <Input
            id="googleClientSecret"
            type="password"
            placeholder={initial.googleClientSecret ?? "GOCSPX-..."}
            value={googleClientSecret}
            onChange={(e) => setGoogleClientSecret(e.target.value)}
            autoComplete="off"
          />
        </div>
      </section>

      {/* Budget */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Budget
        </h2>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="budgetUsd">Soft Cap (USD)</Label>
            <Input
              id="budgetUsd"
              type="number"
              min="0"
              step="0.5"
              value={budgetUsd}
              onChange={(e) => setBudgetUsd(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">Shows warning when exceeded.</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="hardCapUsd">Hard Cap (USD)</Label>
            <Input
              id="hardCapUsd"
              type="number"
              min="0"
              step="1"
              value={hardCapUsd}
              onChange={(e) => setHardCapUsd(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">Blocks all AI ops when exceeded.</p>
          </div>
        </div>
      </section>

      {/* Style Seed */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Caption Style
        </h2>
        <div className="space-y-2">
          <Label htmlFor="styleSeed">Style Seed</Label>
          <textarea
            id="styleSeed"
            className="w-full min-h-[120px] rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="Describe your caption voice: casual, warm, Spanish, short captions under 150 chars..."
            value={styleSeed}
            onChange={(e) => setStyleSeed(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Used as context when generating Instagram captions.
          </p>
        </div>
      </section>

      <Button type="submit" disabled={saving}>
        {saving ? "Saving..." : "Save settings"}
      </Button>
    </form>
  );
}
