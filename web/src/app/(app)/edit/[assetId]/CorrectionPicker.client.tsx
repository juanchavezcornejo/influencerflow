"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

type CorrectionTab = "color" | "crop" | "remove" | "face";
type CorrectionMode = "manual" | "local" | "ai";

export function CorrectionPicker() {
  const [activeTab, setActiveTab] = useState<CorrectionTab>("color");
  const [activeMode, setActiveMode] = useState<CorrectionMode>("local");

  const tabs = [
    { id: "color", label: "Color" },
    { id: "crop", label: "Crop" },
    { id: "remove", label: "Remove" },
    { id: "face", label: "Face" },
  ];

  const modes: { id: CorrectionMode; label: string; enabled: boolean }[] = [
    { id: "manual", label: "🧑 Manual", enabled: true },
    { id: "local", label: "🆓 Local", enabled: true },
    { id: "ai", label: "🤖 IA", enabled: false },
  ];

  const renderContent = () => {
    if (activeTab === "color") {
      return (
        <div className="space-y-3">
          <div className="text-sm font-medium">Correction mode:</div>
          <div className="flex gap-2">
            {modes.map((mode) => (
              <Button
                key={mode.id}
                variant={activeMode === mode.id ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveMode(mode.id)}
                disabled={!mode.enabled}
              >
                {mode.label}
              </Button>
            ))}
          </div>
        </div>
      );
    }

    return (
      <div className="text-sm text-muted-foreground py-3">
        {activeTab === "crop" && "Crop: Coming soon"}
        {activeTab === "remove" && "Object removal: Coming soon"}
        {activeTab === "face" && "Face retouching: Coming soon"}
      </div>
    );
  };

  return (
    <div className="space-y-3">
      {/* Tabs */}
      <div className="flex gap-2">
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === (tab.id as CorrectionTab) ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveTab(tab.id as CorrectionTab)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {/* Tab content */}
      {renderContent()}
    </div>
  );
}
