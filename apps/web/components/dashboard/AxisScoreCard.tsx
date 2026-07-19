import { Sparkline, TREND, ConfidenceBadge } from "@/components/ui/ds";
import type { AxisScore } from "@/lib/types";

const AXIS_LABELS: Record<AxisScore["axis"], string> = {
  founder: "FOUNDER",
  market: "MARKET",
  idea_vs_market: "IDEA ⇄ MARKET",
};

const AXIS_ICON: Record<AxisScore["axis"], React.ReactNode> = {
  founder: (
    <svg width="12" height="12" viewBox="0 0 12 12">
      <circle cx="6" cy="6" r="4.5" fill="none" stroke="var(--ink)" strokeWidth="1.4" />
    </svg>
  ),
  market: (
    <svg width="12" height="12" viewBox="0 0 12 12">
      <rect x="2" y="2" width="8" height="8" fill="none" stroke="var(--ink)" strokeWidth="1.4" transform="rotate(45 6 6)" />
    </svg>
  ),
  idea_vs_market: (
    <svg width="14" height="12" viewBox="0 0 14 12">
      <line x1="1" y1="6" x2="13" y2="6" stroke="var(--ink)" strokeWidth="1.4" />
      <circle cx="3" cy="6" r="2" fill="var(--ink)" />
      <circle cx="11" cy="6" r="2" fill="none" stroke="var(--ink)" strokeWidth="1.4" />
    </svg>
  ),
};

export function formatAxisValue(value: number | string): string {
  return typeof value === "number" ? String(Math.round(value * 100)) : String(value);
}

/**
 * Renders ONE axis. Never combine axis cards into a composite score —
 * this is a binding rule (docs/00-OVERVIEW.md §4 rule 1).
 */
export function AxisScoreCard({
  score,
  history,
}: {
  score: AxisScore;
  history?: number[]; // 0..1, oldest first — 30d trend sparkline
}) {
  const trend = TREND[score.trend];
  const isNumeric = typeof score.value === "number";

  return (
    <div className="rounded-[2px] border border-line bg-surface p-5 transition-colors hover:border-ink">
      <div className="flex items-center justify-between">
        <div className="font-mono text-[11px] tracking-[0.12em] text-sub">
          {AXIS_LABELS[score.axis]}
        </div>
        {AXIS_ICON[score.axis]}
      </div>
      <div className="mt-3.5 flex items-end justify-between">
        <div className="font-serif text-[46px] font-medium leading-none capitalize">
          {formatAxisValue(score.value)}
          {isNumeric && (
            <span className="ml-1 font-mono text-xs normal-case text-faint">/100</span>
          )}
        </div>
        {history && <Sparkline points={history} stroke={trend.color} />}
      </div>
      <div
        className="mt-2 flex items-center gap-1.5 text-[12.5px] font-medium"
        style={{ color: trend.color }}
      >
        <span className="text-sm">{trend.arrow}</span>
        <span>{trend.label}</span>
        <span className="font-mono font-normal text-faint">· 30d</span>
      </div>
      <div className="mt-4 border-t border-line pt-3">
        <ConfidenceBadge confidence={score.confidence} evidenceCount={score.evidence.length} />
        {score.evidence.length > 0 && (
          <div className="mt-3 flex flex-col gap-[7px] text-[12.5px] leading-snug">
            {score.evidence.slice(0, 3).map((ev, i) => (
              <a
                key={i}
                href="#"
                className="w-fit border-b border-dotted border-dotline pb-px no-underline"
              >
                {ev.evidence_snippet} ↗
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function AxisScoreRow({ scores }: { scores: AxisScore[] }) {
  if (scores.length === 0) {
    return (
      <div className="text-sm text-sub italic">
        Not yet analyzed — run 3-axis scoring to populate.
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {scores.map((s) => (
        <AxisScoreCard key={s.axis} score={s} />
      ))}
    </div>
  );
}
