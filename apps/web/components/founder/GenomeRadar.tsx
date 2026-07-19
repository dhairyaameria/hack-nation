"use client";

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import type { FounderGenomeSnapshot } from "@/lib/types";

const DIMENSION_LABELS: Record<string, string> = {
  execution_velocity: "Execution",
  technical_depth: "Technical depth",
  resilience_proxy: "Resilience",
  public_footprint_depth: "Public footprint",
};

/**
 * Genome radar shows 4 core dimensions. `network_embeddedness` is
 * intentionally excluded here and rendered as a separate capped badge
 * (docs/00-OVERVIEW.md §4 rule 7; docs/06-FRONTEND-UX.md §P0.3).
 */
export function GenomeRadar({
  genome,
}: {
  genome: FounderGenomeSnapshot | Record<string, { value: number }> | null | undefined;
}) {
  // Cold-start / outbound founders often have no genome snapshot yet —
  // unknown ≠ zero, so show an empty state instead of a flat radar at 0.
  if (!genome) {
    return (
      <div className="h-64 w-full rounded-lg border bg-muted/30 flex items-center justify-center text-sm text-muted-foreground px-6 text-center">
        No Founder Genome snapshot yet — cold start. Public signals only; not scored as weak.
      </div>
    );
  }

  const data = Object.entries(DIMENSION_LABELS).map(([key, label]) => ({
    dimension: label,
    value: Math.round(((genome as Record<string, { value: number }>)[key]?.value ?? 0) * 100),
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11 }} />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
          <Radar
            name="Genome"
            dataKey="value"
            stroke="#7c5cbf"
            fill="#7c5cbf"
            fillOpacity={0.35}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
