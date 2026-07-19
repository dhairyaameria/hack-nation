import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, FileText } from "lucide-react";
import { getOpportunityDetail } from "@/lib/api/client";
import { AxisScoreRow } from "@/components/dashboard/AxisScoreCard";
import { ContradictionBanner } from "@/components/opportunity/ContradictionBanner";
import { ClaimTrustList } from "@/components/opportunity/ClaimTrustList";
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

  const hasScores = (opp.axis_scores?.length ?? 0) > 0;
  const hasMemo = Boolean(opp.memo?.sections?.length);
  const backHref = opp.source === "inbound" ? "/apply" : "/outbound";
  const backLabel = opp.source === "inbound" ? "Back to inbound sources" : "Back to outbound sources";

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <Link
        href={backHref}
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> {backLabel}
      </Link>

      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">{opp.company_name}</h1>
            <Badge variant={opp.source === "outbound" ? "secondary" : "outline"}>{opp.source}</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            <Link href={`/founders/${opp.founder_id}`} className="hover:underline">
              {opp.founder_name}
            </Link>
          </p>
          {hasMemo && (
            <Link
              href={`/memos/${opp.id}`}
              className="inline-flex items-center gap-1.5 pt-1 text-sm text-foreground/80 hover:text-foreground"
            >
              <FileText className="h-3.5 w-3.5" />
              Open investment memo
            </Link>
          )}
        </div>
        <AnalyzeButton
          opportunityId={opp.id}
          label={hasScores ? "Rerun analysis" : "Run analysis"}
          runningLabel="Analyzing…"
        />
      </header>

      {opp.has_contradiction && <ContradictionBanner />}

      {!hasScores && (
        <div className="rounded-lg border bg-muted/30 p-4">
          <p className="text-sm text-muted-foreground">
            No analysis has run yet for this opportunity. Use <span className="font-medium">Run analysis</span> above
            to start Analyst → Validator → Referee. The investment memo will appear under Investment Memos once analysis finishes.
          </p>
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
    </div>
  );
}
