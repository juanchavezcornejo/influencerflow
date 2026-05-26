"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useCompareSlider } from "@/hooks/use-compare-slider";
import { useToast } from "@/hooks/use-toast";
import { apiFetch } from "@/lib/api-client";
import type { EditVersion, EditCandidatesResponse } from "@/types/api";
import { CorrectionPicker } from "./CorrectionPicker.client";

interface EditViewProps {
  assetId: string;
}

export function EditView({ assetId }: EditViewProps) {
  const router = useRouter();
  const { addToast } = useToast();

  const [proposals, setProposals] = useState<EditVersion[]>([]);
  const [current, setCurrent] = useState<EditVersion | null>(null);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);

  const slider = useCompareSlider(50);

  // Load proposals on mount
  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await apiFetch<EditCandidatesResponse>(`/assets/${assetId}/edits/suggest`, {
          method: "POST",
          body: { corrections: ["color"], mode: "local" },
        });

        setProposals(data.proposals);
        setCurrent(data.current);
        setSelectedIdx(0);
      } catch (err) {
        addToast((err as Error).message, "error");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [assetId, addToast]);

  const handleAccept = async () => {
    if (!proposals[selectedIdx]) return;

    try {
      setAccepting(true);
      await apiFetch<void>(`/edits/${proposals[selectedIdx].id}/accept`, {
        method: "POST",
        body: { selected_corrections: ["color"] },
      });

      addToast("Edit accepted. Processing full image...", "success");
      // Redirect back to session after a delay
      setTimeout(() => router.back(), 1500);
    } catch (err) {
      addToast((err as Error).message, "error");
    } finally {
      setAccepting(false);
    }
  };

  const handleReject = async (regenerate: boolean) => {
    if (!proposals[selectedIdx]) return;

    try {
      setLoading(true);
      await apiFetch<void>(`/edits/${proposals[selectedIdx].id}/reject`, {
        method: "POST",
        body: { regenerate },
      });

      if (regenerate) {
        // Reload proposals
        const data = await apiFetch<EditCandidatesResponse>(`/assets/${assetId}/edits/suggest`, {
          method: "POST",
          body: { corrections: ["color"], mode: "local" },
        });
        setProposals(data.proposals);
        setSelectedIdx(0);
      } else {
        // Go back
        router.back();
      }
    } catch (err) {
      addToast((err as Error).message, "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        setSelectedIdx((prev) => (prev > 0 ? prev - 1 : proposals.length - 1));
      } else if (e.key === "ArrowRight") {
        setSelectedIdx((prev) => (prev < proposals.length - 1 ? prev + 1 : 0));
      } else if (e.key === "Enter") {
        handleAccept();
      } else if (e.key === "Escape") {
        router.back();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [proposals, selectedIdx, router, handleAccept]);

  if (loading || !current) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground">Loading edits...</div>
      </div>
    );
  }

  const selectedProposal = proposals[selectedIdx];

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Before/After Slider */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div
          ref={slider.containerRef}
          className="relative w-full h-full max-w-2xl max-h-2xl overflow-hidden rounded-lg shadow-lg"
        >
          {/* Before panel */}
          <img
            src={`/api/v1/assets/${assetId}/preview`}
            alt="Before"
            className="absolute inset-0 w-full h-full object-cover"
          />

          {/* After panel */}
          <div
            className="absolute inset-0 overflow-hidden"
            style={{ width: `${slider.position}%` }}
          >
            <img
              src={`/api/v1/edits/${selectedProposal?.id}/preview`}
              alt="After"
              className="absolute inset-0 w-full h-full object-cover"
              style={{ width: `${100 / Math.max(slider.position, 1)}%` }}
            />
          </div>

          {/* Slider handle */}
          <div
            className="absolute top-0 bottom-0 w-1 bg-white cursor-col-resize shadow-lg"
            style={{ left: `${slider.position}%` }}
            {...slider.handleProps}
          >
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full shadow-lg" />
          </div>
        </div>
      </div>

      {/* Controls Panel */}
      <Card className="m-4 p-4 bg-card border">
        {/* Proposal tabs */}
        <div className="flex gap-2 mb-4">
          {proposals.map((proposal, idx) => {
            const pName: string | undefined =
              (proposal.correctionsAppliedJson?.display_name as string | undefined) ||
              (proposal.correctionsAppliedJson?.preset as string | undefined);
            return (
              <Button
                key={idx}
                variant={idx === selectedIdx ? "default" : "outline"}
                onClick={() => setSelectedIdx(idx)}
                size="sm"
              >
                {idx + 1}: {pName ?? proposal.changesLogText}
              </Button>
            );
          })}
        </div>

        {/* Correction picker */}
        <div className="mb-4">
          <CorrectionPicker />
        </div>

        {/* Changes log */}
        {selectedProposal?.changesLogText && (
          <div className="mb-4 p-3 bg-muted rounded text-sm font-mono whitespace-pre-wrap">
            {selectedProposal.changesLogText}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-2 justify-end">
          <Button variant="outline" onClick={() => handleReject(false)} disabled={accepting}>
            Reject
          </Button>
          <Button variant="outline" onClick={() => handleReject(true)} disabled={accepting}>
            Regenerate
          </Button>
          <Button onClick={handleAccept} disabled={accepting}>
            {accepting ? "Processing..." : "Accept"}
          </Button>
        </div>

        {/* Cost badge */}
        <div className="mt-4 text-sm text-muted-foreground">
          🆓 Free local corrections
        </div>
      </Card>
    </div>
  );
}
