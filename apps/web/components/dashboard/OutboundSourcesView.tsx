"use client";

import { useState } from "react";
import { OpportunityCard } from "@/components/dashboard/OpportunityCard";
import { SlaTimer } from "@/components/dashboard/SlaTimer";
import { FindLeadPanel } from "@/components/sourcing/FindLeadPanel";
import { Badge } from "@/components/ui/badge";
import type { OpportunitySummary } from "@/lib/types";

interface Props {
  thesisName: string;
  opportunities: OpportunitySummary[];
}

export function OutboundSourcesView({ thesisName, opportunities }: Props) {
  const [findLeadOpen, setFindLeadOpen] = useState(false);
  const liveSla = opportunities.find((o) => o.sla?.signal_at && !o.sla?.decision_at);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Outbound Sources</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Active thesis:{" "}
            <Badge variant="outline" className="ml-1">
              {thesisName}
            </Badge>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground text-right hidden sm:block">
            {opportunities.length} opportunities in pipeline
          </span>
          <button
            type="button"
            onClick={() => setFindLeadOpen((v) => !v)}
            className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium shrink-0"
          >
            {findLeadOpen ? "Hide Find Lead" : "Find Lead"}
          </button>
        </div>
      </header>

      <FindLeadPanel open={findLeadOpen} onClose={() => setFindLeadOpen(false)} />

      {liveSla && (
        <div className="max-w-sm">
          <SlaTimer sla={liveSla.sla} />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {opportunities.map((opp) => (
          <OpportunityCard key={opp.id} opp={opp} />
        ))}
      </div>
    </div>
  );
}
