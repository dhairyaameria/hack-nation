"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { analyzeOpportunity } from "@/lib/api/client";

export function AnalyzeButton({
  opportunityId,
  label = "Run analysis",
  runningLabel = "Running Analyst → Validator → Referee…",
  className = "rounded-md bg-primary text-primary-foreground px-3 py-1.5 text-sm font-medium disabled:opacity-50",
  stopPropagation = false,
}: {
  opportunityId: string;
  label?: string;
  runningLabel?: string;
  className?: string;
  /** Use when nested inside a Link/card so click doesn't navigate */
  stopPropagation?: boolean;
}) {
  const router = useRouter();
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick(e: React.MouseEvent) {
    if (stopPropagation) {
      e.preventDefault();
      e.stopPropagation();
    }
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
    <div className="flex flex-col gap-1.5">
      <button
        type="button"
        onClick={handleClick}
        disabled={running}
        className={className}
      >
        {running ? runningLabel : label}
      </button>
      {error && <span className="text-xs text-bad">{error}</span>}
    </div>
  );
}
