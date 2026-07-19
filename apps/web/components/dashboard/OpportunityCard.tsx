"use client";

import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, ArrowUpRight, Radar } from "lucide-react";
import type { OpportunitySummary } from "@/lib/types";
import { AxisScoreRow } from "./AxisScoreCard";

export function OpportunityCard({ opp }: { opp: OpportunitySummary }) {
  const router = useRouter();

  return (
    <Card
      role="link"
      tabIndex={0}
      className="transition-shadow hover:shadow-md cursor-pointer group"
      onClick={() => router.push(`/opportunities/${opp.id}`)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          router.push(`/opportunities/${opp.id}`);
        }
      }}
    >
      <CardHeader className="flex flex-row items-start justify-between gap-2 pb-2">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold leading-none">{opp.company_name}</h3>
            <Badge variant={opp.source === "outbound" ? "secondary" : "outline"}>
              {opp.source}
            </Badge>
            {opp.has_contradiction && (
              <Badge variant="destructive" className="gap-1">
                <AlertTriangle className="h-3 w-3" /> Contradiction
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">{opp.founder_name}</p>
        </div>
        <ArrowUpRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
      </CardHeader>
      <CardContent className="space-y-3">
        {opp.discovery_channel && (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Radar className="h-3.5 w-3.5" />
            {opp.triggering_signal ?? opp.discovery_channel}
          </div>
        )}
        <AxisScoreRow scores={opp.axis_scores} />
        <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
          <span>Status: {opp.status}</span>
          {opp.thesis_fit_score != null && (
            <span>Thesis fit: {Math.round(opp.thesis_fit_score * 100)}%</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
