import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { getOpportunityDetail } from "@/lib/api/client";
import { AxisScoreRow } from "@/components/dashboard/AxisScoreCard";
import { ContradictionBanner } from "@/components/opportunity/ContradictionBanner";
import { ClaimTrustList } from "@/components/opportunity/ClaimTrustList";
import { MemoView } from "@/components/opportunity/MemoView";
import { AnalyzeButton } from "@/components/opportunity/AnalyzeButton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

export const dynamic = "force-dynamic";

export default async function OpportunityDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const opp = await getOpportunityDetail(id);
  if (!opp) notFound();

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <Link href="/outbound" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to outbound sources
      </Link>

      <header className="space-y-1">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-tight">{opp.company_name}</h1>
          <Badge variant={opp.source === "outbound" ? "secondary" : "outline"}>{opp.source}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          <Link href={`/founders/${opp.founder_id}`} className="hover:underline">
            {opp.founder_name}
          </Link>
        </p>
      </header>

      {opp.has_contradiction && <ContradictionBanner />}

      {(!opp.axis_scores || opp.axis_scores.length === 0) && (
        <div className="rounded-lg border bg-muted/30 p-4">
          <p className="text-sm text-muted-foreground mb-3">
            No analysis has run yet for this opportunity.
          </p>
          <AnalyzeButton opportunityId={opp.id} />
        </div>
      )}

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Three-Axis Score
        </h2>
        <AxisScoreRow scores={opp.axis_scores} />
      </section>

      <Separator />

      <section className="space-y-3">
        <div>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Evidence &amp; Trust
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Narrative analysis with inline citations — expand Sources for the full trace.
          </p>
        </div>
        <ClaimTrustList claims={opp.claims ?? []} />
      </section>

      <Separator />

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Investment Memo
        </h2>
        <MemoView memo={opp.memo} />
      </section>
    </div>
  );
}
