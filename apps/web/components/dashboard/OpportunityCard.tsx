"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { OpportunitySummary, AxisScore } from "@/lib/types";
import { DiscoveryChannelBadge, TREND } from "@/components/ui/ds";
import { formatAxisValue } from "./AxisScoreCard";

const AXIS_SHORT: Record<AxisScore["axis"], string> = {
  founder: "FOUNDER",
  market: "MARKET",
  idea_vs_market: "IDEA ⇄ MKT",
};

const SLA_TOTAL_H = 24;
const SLA_WARN_H = 12;

function SlaChip({ signalAt }: { signalAt: string | null }) {
  const [now, setNow] = useState<number | null>(null);

  useEffect(() => {
    setNow(Date.now());
  }, []);

  if (!signalAt) return null;
  // Stable until mount so SSR matches the first client paint.
  if (now == null) {
    return (
      <span
        className="whitespace-nowrap rounded-[2px] border px-2.5 py-1 font-mono text-[11px]"
        style={{ color: "var(--ink)", background: "var(--background)", borderColor: "var(--line)" }}
      >
        ◷ SLA
      </span>
    );
  }

  const h = SLA_TOTAL_H - (now - new Date(signalAt).getTime()) / 3_600_000;
  const urgent = h < SLA_WARN_H;
  const txt =
    h <= 0
      ? "SLA breached"
      : h >= 24
        ? `${Math.floor(h / 24)}d ${Math.round(h % 24)}h remaining`
        : `${Math.floor(h)}h ${Math.round((h % 1) * 60)}m remaining`;
  return (
    <span
      className="whitespace-nowrap rounded-[2px] border px-2.5 py-1 font-mono text-[11px]"
      style={
        urgent
          ? { color: "var(--bad-ink)", background: "var(--bad-bg)", borderColor: "var(--bad-line)" }
          : { color: "var(--ink)", background: "var(--background)", borderColor: "var(--line)" }
      }
    >
      ◷ {txt}
    </span>
  );
}

/** Pipeline row — see design doc component 07. */
export function OpportunityCard({ opp }: { opp: OpportunitySummary }) {
  return (
    <Link
      href={`/opportunities/${opp.id}`}
      className="block border-b border-line2 border-l-2 border-l-transparent px-5 py-5 !text-ink no-underline transition-colors hover:border-l-brand hover:bg-raise"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="font-serif text-xl font-semibold">{opp.company_name}</span>
            <DiscoveryChannelBadge channel={opp.discovery_channel ?? opp.source} />
            {opp.has_contradiction && (
              <span className="rounded-[2px] px-[7px] py-[3px] font-mono text-[9.5px] uppercase tracking-[0.06em] text-bad bg-bad-bg">
                Contradiction
              </span>
            )}
          </div>
          {opp.triggering_signal && (
            <div className="mt-1 text-[13px] text-sub">{opp.triggering_signal}</div>
          )}
          <div className="mt-1.5 font-mono text-[11px]">{opp.founder_name}</div>
        </div>
        <div className="flex shrink-0 items-center gap-3.5">
          {opp.thesis_fit_score != null && (
            <span className="font-mono text-[10.5px] text-sub">
              FIT {Math.round(opp.thesis_fit_score * 100)}%
            </span>
          )}
          <SlaChip signalAt={opp.sla.signal_at} />
        </div>
      </div>
      {opp.axis_scores.length > 0 && (
        <div className="mt-4 grid grid-cols-3 rounded-[2px] border border-line2">
          {opp.axis_scores.map((a) => {
            const trend = TREND[a.trend];
            return (
              <div
                key={a.axis}
                className="flex items-center justify-between gap-2.5 border-l border-line2 first:border-l-0 px-3.5 py-2.5"
              >
                <div>
                  <div className="font-mono text-[9.5px] tracking-[0.1em] text-sub">
                    {AXIS_SHORT[a.axis]}
                  </div>
                  <div className="mt-0.5 flex items-baseline gap-1.5">
                    <span className="font-serif text-[21px] font-semibold capitalize">
                      {formatAxisValue(a.value)}
                    </span>
                    <span className="text-xs font-medium" style={{ color: trend.color }}>
                      {trend.arrow} {trend.label}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Link>
  );
}
