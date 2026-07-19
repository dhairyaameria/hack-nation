import Link from "next/link";
import { ArrowRight, FileText } from "lucide-react";
import { getMemos } from "@/lib/api/client";
import { SectionLabel, DiscoveryChannelBadge } from "@/components/ui/ds";
import { InvestButton } from "@/components/opportunity/InvestButton";

export const dynamic = "force-dynamic";

/** Bar showing filled sections vs. flagged gaps — gaps are never hidden. */
function CompletenessBar({ filled, gaps, total }: { filled: number; gaps: number; total: number }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex gap-[3px]">
        {Array.from({ length: total }, (_, i) => (
          <span
            key={i}
            className="h-2 w-5 rounded-[1px]"
            style={{ background: i < filled ? "var(--brand)" : "var(--line2)" }}
          />
        ))}
      </div>
      <span className="font-mono text-[10.5px] text-sub">
        {filled}/{total}
        {gaps > 0 && <span className="text-brand-ink"> · {gaps} gap{gaps > 1 ? "s" : ""}</span>}
      </span>
    </div>
  );
}

export default async function InvestmentMemosPage() {
  const memos = await getMemos();
  const totalGaps = memos.reduce((n, m) => n + m.gaps_flagged, 0);
  const contradictions = memos.filter((m) => m.has_contradiction).length;

  return (
    <div className="mx-auto max-w-[1100px] px-10 pb-24 pt-14">
      <div className="border-b border-ink pb-7">
        <h1 className="mt-3.5 font-serif text-[44px] font-medium leading-[1.05] tracking-[-0.01em]">
          Investment memos
        </h1>
      </div>
      {memos.length === 0 ? (
        <div className="mt-8 rounded-[2px] border border-dashed border-line3 px-6 py-14 text-center">
          <FileText className="mx-auto h-7 w-7 text-faint" />
          <p className="mt-3 text-[13px] text-sub">
            No memos yet. Run analysis on an inbound or outbound opportunity — the memo appears here
            when it finishes.
          </p>
          <Link href="/" className="mt-1 inline-block font-mono text-[11px] uppercase tracking-[0.06em]">
            Go to pipeline →
          </Link>
        </div>
      ) : (
        <div className="mt-6 rounded-[2px] border border-line bg-surface">
          <div className="flex items-center justify-between border-b border-line px-5 py-3 font-mono text-[10.5px] uppercase tracking-[0.1em] text-sub">
            <span>All memos</span>
            <span>Sorted by last updated</span>
          </div>
          {memos.map((memo) => {
            const approved =
              memo.status === "funded" ||
              memo.recommendation === "yes" ||
              Boolean(memo.decision_at);
            return (
              <div
                key={memo.id}
                className="flex items-stretch gap-3 border-b border-line2 border-l-2 border-l-transparent px-5 py-5 transition-colors last:border-b-0 hover:border-l-brand hover:bg-raise"
              >
                <Link
                  href={`/memos/${memo.id}`}
                  className="min-w-0 flex-1 !text-ink no-underline"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2.5">
                        <span className="font-serif text-xl font-semibold hover:underline underline-offset-2">
                          {memo.company_name}
                        </span>
                        {memo.source && <DiscoveryChannelBadge channel={memo.source} />}
                        {memo.has_contradiction && (
                          <span className="rounded-[2px] border border-brand/30 bg-accent px-[7px] py-[3px] font-mono text-[9.5px] uppercase tracking-[0.06em] text-brand-ink">
                            Contradiction
                          </span>
                        )}
                      </div>
                      <div className="mt-1 font-mono text-[11px] text-sub">{memo.founder_name}</div>
                    </div>
                    <div className="flex shrink-0 items-center gap-4">
                      <CompletenessBar
                        filled={memo.sections_filled}
                        gaps={memo.gaps_flagged}
                        total={memo.section_count}
                      />
                      <ArrowRight className="h-4 w-4 text-faint" />
                    </div>
                  </div>
                  {memo.snapshot && (
                    <p className="mt-2.5 max-w-[760px] text-[13px] leading-relaxed text-sub">
                      {memo.snapshot}
                    </p>
                  )}
                  {memo.updated_at && (
                    <div className="mt-2 font-mono text-[10px] uppercase tracking-[0.06em] text-faint">
                      Updated {new Date(memo.updated_at).toLocaleString()}
                    </div>
                  )}
                </Link>
                <div className="flex shrink-0 items-center self-center">
                  <InvestButton
                    opportunityId={memo.opportunity_id}
                    alreadyApproved={approved}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
