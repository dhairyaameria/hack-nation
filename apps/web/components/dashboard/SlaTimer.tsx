"use client";

import { useEffect, useState } from "react";
import { Clock } from "lucide-react";
import type { SlaTimestamps } from "@/lib/types";

const STAGES: { key: keyof SlaTimestamps; label: string }[] = [
  { key: "signal_at", label: "Signal" },
  { key: "screening_at", label: "Screening" },
  { key: "diligence_at", label: "Diligence" },
  { key: "decision_at", label: "Decision" },
];

/**
 * Live "signal → decision" clock — proves the 24h SLA claim.
 * See docs/06-FRONTEND-UX.md §P0.1.
 */
export function SlaTimer({ sla }: { sla: SlaTimestamps }) {
  // Defer Date.now() until after mount so SSR HTML matches the first client paint.
  const [now, setNow] = useState<number | null>(null);

  useEffect(() => {
    setNow(Date.now());
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  if (!sla.signal_at) return null;

  const signalMs = new Date(sla.signal_at).getTime();
  const elapsedMs = now == null ? 0 : Math.max(0, now - signalMs);
  const totalMs = 24 * 60 * 60 * 1000;
  const pctElapsed = Math.min(100, (elapsedMs / totalMs) * 100);
  const hours = Math.floor(elapsedMs / 3_600_000);
  const minutes = Math.floor((elapsedMs % 3_600_000) / 60_000);
  const seconds = Math.floor((elapsedMs % 60_000) / 1000);

  const currentStageIdx = STAGES.reduce(
    (acc, s, i) => (sla[s.key] ? i : acc),
    0
  );

  return (
    <div className="rounded-md border bg-card p-3">
      <div className="flex items-center justify-between text-xs font-medium text-muted-foreground mb-2">
        <span className="flex items-center gap-1.5">
          <Clock className="h-3.5 w-3.5" /> Decision SLA
        </span>
        <span className="tabular-nums">
          {hours}h {minutes}m {seconds}s / 24h
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full bg-primary transition-all"
          style={{ width: `${pctElapsed}%` }}
        />
      </div>
      <div className="flex justify-between mt-1.5">
        {STAGES.map((s, i) => (
          <span
            key={s.key}
            className={
              i <= currentStageIdx
                ? "text-[11px] font-medium text-foreground"
                : "text-[11px] text-muted-foreground"
            }
          >
            {s.label}
          </span>
        ))}
      </div>
    </div>
  );
}
