import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AxisScore } from "@/lib/types";

const AXIS_LABELS: Record<AxisScore["axis"], string> = {
  founder: "Founder",
  market: "Market",
  idea_vs_market: "Idea vs. Market",
};

const TREND_ICON = {
  improving: TrendingUp,
  declining: TrendingDown,
  stable: Minus,
};

const TREND_COLOR = {
  improving: "text-emerald-600",
  declining: "text-red-600",
  stable: "text-muted-foreground",
};

/**
 * Renders ONE axis. Never combine axis cards into a composite score —
 * this is a binding rule (docs/00-OVERVIEW.md §4 rule 1).
 */
export function AxisScoreCard({ score }: { score: AxisScore }) {
  const TrendIcon = TREND_ICON[score.trend];
  const isNumeric = typeof score.value === "number";

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {AXIS_LABELS[score.axis]}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-semibold tabular-nums">
            {isNumeric ? `${Math.round((score.value as number) * 100)}` : String(score.value)}
            {isNumeric && <span className="text-sm text-muted-foreground">/100</span>}
          </span>
          <span className={cn("flex items-center gap-1 text-xs font-medium", TREND_COLOR[score.trend])}>
            <TrendIcon className="h-3.5 w-3.5" />
            {score.trend}
          </span>
        </div>
        <div className="mt-1 text-xs text-muted-foreground">
          confidence {Math.round(score.confidence * 100)}%
        </div>
        {score.evidence.length > 0 && (
          <div className="mt-2 space-y-1 border-t pt-2">
            {score.evidence.map((e, i) => (
              <p
                key={i}
                className={cn(
                  "text-[11px] leading-snug",
                  e.source_type === "network_proximity" ? "text-amber-700" : "text-muted-foreground"
                )}
              >
                {e.evidence_snippet}
              </p>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function AxisScoreRow({ scores }: { scores: AxisScore[] }) {
  if (scores.length === 0) {
    return (
      <div className="text-sm text-muted-foreground italic">
        Not yet analyzed — run 3-axis scoring to populate.
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {scores.map((s) => (
        <AxisScoreCard key={s.axis} score={s} />
      ))}
    </div>
  );
}
