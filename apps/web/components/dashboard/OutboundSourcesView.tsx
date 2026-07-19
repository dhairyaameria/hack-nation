"use client";

import { useState } from "react";
import { OutboundOpportunityCard } from "@/components/dashboard/OutboundOpportunityCard";
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
    <div className="p-8 max-w-6xl mx-auto space-y-8">
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
            {opportunities.length} in pipeline
          </span>
          <button
            type="button"
            onClick={() => setFindLeadOpen(true)}
            className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium shrink-0"
          >
            Find Lead
          </button>
        </div>
      </header>

      {/* Overlay drawer — does not push the card grid */}
      <FindLeadPanel open={findLeadOpen} onClose={() => setFindLeadOpen(false)} />

      {liveSla && (
        <div className="max-w-sm">
          <SlaTimer sla={liveSla.sla} />
        </div>
      )}

      {opportunities.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No outbound opportunities yet. Use Find Lead to discover founders.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {opportunities.map((opp) => (
            <OutboundOpportunityCard key={opp.id} opp={opp} />
          ))}
        </div>
      )}
    </div>
  );
}
