import { getPipelineDashboard } from "@/lib/api/client";
import { OpportunityCard } from "@/components/dashboard/OpportunityCard";
import { SlaTimer } from "@/components/dashboard/SlaTimer";
import { Badge } from "@/components/ui/badge";

export const dynamic = "force-dynamic";

export default async function PipelinePage() {
  const dashboard = await getPipelineDashboard();
  const opportunities = dashboard.opportunities;
  const liveSla = opportunities.find((o) => o.sla?.signal_at && !o.sla?.decision_at);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Pipeline</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Active thesis:{" "}
            <Badge variant="outline" className="ml-1">
              {dashboard.active_thesis.name}
            </Badge>
          </p>
        </div>
        <div className="text-sm text-muted-foreground text-right">
          {opportunities.length} opportunities in pipeline
        </div>
      </header>

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
