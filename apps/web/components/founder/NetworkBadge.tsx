import { Network } from "lucide-react";
import type { NetworkProximity } from "@/lib/types";

/**
 * SEPARATE from the Genome radar — network proximity never dominates
 * merit and is always disclosed in plain language (docs/00-OVERVIEW.md §4 rule 7).
 */
export function NetworkBadge({ proximity }: { proximity: NetworkProximity | null }) {
  if (!proximity) {
    return (
      <div className="rounded-md border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
        No network proximity data available.
      </div>
    );
  }

  return (
    <div className="rounded-md border bg-amber-50 border-amber-200 px-3 py-2.5 space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-sm font-medium text-amber-900">
          <Network className="h-3.5 w-3.5" /> Network embeddedness
        </span>
        <span className="text-sm font-semibold tabular-nums text-amber-900">
          {Math.round(proximity.proximity_score * 100)}
          <span className="text-xs text-amber-700">/100</span>
        </span>
      </div>
      <p className="text-xs text-amber-800 leading-snug">{proximity.disclosure}</p>
    </div>
  );
}
