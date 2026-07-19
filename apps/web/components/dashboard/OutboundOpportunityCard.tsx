"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { DiscoveryChannelBadge } from "@/components/ui/ds";
import { CompanyMark } from "@/components/company/CompanyMark";
import { companyImageCandidates } from "@/lib/companyImage";
import type { OpportunitySummary } from "@/lib/types";

function channelsFor(opp: OpportunitySummary): string[] {
  if (opp.source_channels?.length) return opp.source_channels;
  const raw = opp.discovery_channel || opp.source;
  return raw
    .split(/[,|;]+/)
    .map((c) => c.trim().toLowerCase())
    .filter(Boolean);
}

export function OutboundOpportunityCard({ opp }: { opp: OpportunitySummary }) {
  const candidates = companyImageCandidates(opp.company_name, opp.company_domain);
  const [failed, setFailed] = useState(false);
  const imgSrc = !failed && candidates[0] ? candidates[0] : null;
  const sources = channelsFor(opp);

  return (
    <Link
      href={`/opportunities/${opp.id}`}
      className="group flex flex-col overflow-hidden rounded-xl border border-border/80 bg-background no-underline transition hover:border-brand-ink/40 hover:shadow-sm"
    >
      <div className="relative aspect-[4/3] overflow-hidden">
        {imgSrc ? (
          // eslint-disable-next-line @next/next/no-img-element -- external logo CDN with mark fallback
          <img
            src={imgSrc}
            alt=""
            className="h-full w-full object-contain bg-muted/30 p-8 transition group-hover:scale-[1.02]"
            onError={() => setFailed(true)}
          />
        ) : (
          <CompanyMark name={opp.company_name} />
        )}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-background to-transparent" />
      </div>

      <div className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-base font-semibold tracking-tight text-foreground group-hover:text-brand-ink">
            {opp.company_name}
          </h3>
          {opp.has_contradiction && (
            <Badge variant="outline" className="shrink-0 text-[10px] text-bad border-bad/30">
              contradiction
            </Badge>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5">
          {sources.length === 0 ? (
            <Badge variant="outline" className="text-[10px] font-normal">
              outbound
            </Badge>
          ) : (
            sources.map((ch) => (
              <DiscoveryChannelBadge key={ch} channel={ch} className="!text-[10px]" />
            ))
          )}
        </div>
      </div>
    </Link>
  );
}
