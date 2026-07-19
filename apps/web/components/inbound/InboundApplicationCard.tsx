"use client";

import Link from "next/link";
import { FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { deckAbsoluteUrl, type InboundApplication } from "@/lib/api/client";

const VERDICT_STYLE: Record<string, string> = {
  pass: "bg-good-bg text-good border-good/30",
  reject: "bg-bad-bg text-bad border-bad-line",
  "needs-more-info": "bg-warn-bg text-warn border-warn-line",
};

export function InboundApplicationCard({ app }: { app: InboundApplication }) {
  const href = app.company_id
    ? `/companies/${app.company_id}`
    : `/opportunities/${app.id}`;
  const pdfUrl = deckAbsoluteUrl(app.deck_url);

  return (
    <Link
      href={href}
      className="group flex flex-col overflow-hidden rounded-xl border border-border/80 bg-background no-underline transition hover:border-brand-ink/40 hover:shadow-sm"
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-muted/40">
        {pdfUrl ? (
          <iframe
            title={`${app.company_name} deck preview`}
            src={`${pdfUrl}#page=1&view=FitH&toolbar=0&navpanes=0`}
            className="pointer-events-none h-[140%] w-full origin-top scale-[1.02] border-0"
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
            <FileText className="h-10 w-10 opacity-40" />
            <span className="text-xs">No deck uploaded</span>
          </div>
        )}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-background to-transparent" />
      </div>

      <div className="space-y-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-base font-semibold tracking-tight text-foreground group-hover:text-brand-ink">
            {app.company_name}
          </h3>
          {app.screen_verdict && (
            <Badge
              variant="outline"
              className={`shrink-0 text-[10px] ${VERDICT_STYLE[app.screen_verdict] ?? ""}`}
            >
              {app.screen_verdict}
            </Badge>
          )}
        </div>
        <p className="text-sm text-muted-foreground">{app.founder_name}</p>
        <div className="flex flex-wrap gap-1.5">
          {app.company_sector && (
            <Badge variant="secondary" className="text-[10px] font-normal">
              {app.company_sector}
            </Badge>
          )}
          {app.company_stage && (
            <Badge variant="outline" className="text-[10px] font-normal">
              {app.company_stage}
            </Badge>
          )}
          {app.has_deck && (
            <Badge variant="outline" className="text-[10px] font-normal">
              PDF
            </Badge>
          )}
        </div>
      </div>
    </Link>
  );
}
