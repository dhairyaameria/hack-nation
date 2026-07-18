"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { analyzeOpportunity } from "@/lib/api/client";

export function AnalyzeButton({ opportunityId }: { opportunityId: string }) {
  const router = useRouter();
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setRunning(true);
    setError(null);
    try {
      await analyzeOpportunity(opportunityId);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={handleClick}
        disabled={running}
        className="rounded-md bg-primary text-primary-foreground px-3 py-1.5 text-sm font-medium disabled:opacity-50"
      >
        {running ? "Running Analyst → Validator → Referee…" : "Run analysis"}
      </button>
      {error && <span className="text-sm text-red-600">{error}</span>}
    </div>
  );
}
