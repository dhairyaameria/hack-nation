import Link from "next/link";
import { AlertTriangle, FileText } from "lucide-react";
import { getMemos } from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";

export const dynamic = "force-dynamic";

export default async function InvestmentMemosPage() {
  const memos = await getMemos();

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Investment Memos</h1>
        <p className="text-sm text-muted-foreground">
          All generated memos — company snapshot, hypotheses, SWOT, problem &amp; product,
          traction. Gap flags stay visible; nothing is fabricated to fill a blank.
        </p>
      </header>

      {memos.length === 0 ? (
        <div className="rounded-lg border border-dashed p-10 text-center space-y-2">
          <FileText className="h-8 w-8 mx-auto text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No memos yet. Run Analyze on an opportunity to generate one.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {memos.map((memo) => (
            <Link
              key={memo.id}
              href={`/opportunities/${memo.opportunity_id}`}
              className="block rounded-lg border p-4 space-y-2 hover:border-primary/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium">
                    {memo.company_name}
                    <span className="text-muted-foreground font-normal"> — {memo.founder_name}</span>
                  </p>
                  {memo.updated_at && (
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Updated {new Date(memo.updated_at).toLocaleString()}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {memo.source && (
                    <Badge variant={memo.source === "outbound" ? "secondary" : "outline"}>
                      {memo.source}
                    </Badge>
                  )}
                  {memo.has_contradiction && (
                    <Badge variant="destructive" className="gap-1">
                      <AlertTriangle className="h-3 w-3" /> Contradiction
                    </Badge>
                  )}
                </div>
              </div>

              {memo.snapshot && (
                <p className="text-sm text-muted-foreground line-clamp-2">{memo.snapshot}</p>
              )}

              <p className="text-xs text-muted-foreground">
                {memo.sections_filled}/{memo.section_count} sections filled
                {memo.gaps_flagged > 0 && (
                  <span className="text-amber-700"> · {memo.gaps_flagged} gap(s) flagged</span>
                )}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
