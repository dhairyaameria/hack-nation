"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { analyzeOpportunity } from "@/lib/api/client";

export function AnalyzeButton({
  opportunityId,
  label = "Run analysis",
  runningLabel = "Analyzing",
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
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // The analyze call runs live research + per-claim validation and takes
  // ~1-2 minutes; a ticking counter is the difference between "working"
  // and "frozen" from the user's side.
  useEffect(() => {
    if (!running) return;
    setElapsed(0);
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [running]);

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
        {running ? `${runningLabel.replace(/…$/, "")}… ${elapsed}s` : label}
      </button>
      {running && (
        <span className="text-xs text-muted-foreground">
          Live research → claim validation → memo → bear case. Usually 1–2 min.
        </span>
      )}
      {error && <span className="text-xs text-bad">{error}</span>}
    </div>
  );
}
