import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ClaimTrust } from "@/lib/types";

const STATUS_STYLE: Record<ClaimTrust["validation_status"], string> = {
  verified: "bg-emerald-100 text-emerald-800 border-emerald-200",
  contradicted: "bg-red-100 text-red-800 border-red-200",
  weakly_supported: "bg-amber-100 text-amber-800 border-amber-200",
  unknown: "bg-zinc-100 text-zinc-700 border-zinc-200",
};

const STATUS_LABEL: Record<ClaimTrust["validation_status"], string> = {
  verified: "Verified",
  contradicted: "Contradicted",
  weakly_supported: "Weakly supported",
  unknown: "Unknown",
};

/** Per-claim Trust Score with evidence drill-down (docs/00-OVERVIEW.md §4 rule 2). */
export function ClaimTrustList({ claims }: { claims: ClaimTrust[] }) {
  if (claims.length === 0) {
    return <p className="text-sm text-muted-foreground italic">No claims extracted yet.</p>;
  }

  return (
    <div className="space-y-3">
      {claims.map((claim) => (
        <Card key={claim.claim_id} className={cn(claim.validation_status === "contradicted" && "border-red-300")}>
          <CardContent className="pt-4 space-y-2">
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm font-medium">{claim.text}</p>
              <Badge className={cn("border shrink-0", STATUS_STYLE[claim.validation_status])}>
                {STATUS_LABEL[claim.validation_status]}
              </Badge>
            </div>
            <div className="text-xs text-muted-foreground">
              Trust score: {Math.round(claim.trust_score * 100)}/100
            </div>
            <div className="space-y-1.5 border-t pt-2">
              {claim.evidence.map((ev, i) => (
                <div key={i} className="text-xs flex gap-2">
                  <span className="text-muted-foreground shrink-0">
                    [{ev.source_type} · {ev.source_locator}]
                  </span>
                  <span className="text-foreground/80">&ldquo;{ev.evidence_snippet}&rdquo;</span>
                  <span className="text-muted-foreground shrink-0 ml-auto">
                    {Math.round(ev.confidence * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
