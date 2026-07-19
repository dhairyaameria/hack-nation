import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ArrowUpRight } from "lucide-react";
import { getMemoDetail, type MemoSectionDetail } from "@/lib/api/client";
import { DiscoveryChannelBadge, DisclosureBadge } from "@/components/ui/ds";
import { EvidenceCard } from "@/components/opportunity/EvidenceCard";
import { InvestButton } from "@/components/opportunity/InvestButton";
import { memoGapCopy, memoGapKind } from "@/lib/utils";
import type { EvidenceRef, ValidationStatus } from "@/lib/types";

export const dynamic = "force-dynamic";

/**
 * A section is only as trustworthy as what backs it. Sections with no evidence
 * say so rather than rendering as bare assertions.
 */
function MemoSection({ section, index }: { section: MemoSectionDetail; index: number }) {
  const n = String(index + 1).padStart(2, "0");
  const empty = !section.content;
  const gap = empty ? memoGapKind(section.title, Boolean(section.not_disclosed)) : null;

  return (
    <section className="border-t border-line py-8 first:border-t-0">
      <div className="flex items-baseline justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <span className="font-mono text-[11px] tracking-[0.14em] text-faint">{n}</span>
          <h2 className="font-serif text-[24px] font-medium">{section.title}</h2>
        </div>
        {gap === "withheld" && <DisclosureBadge kind="not_disclosed" />}
        {gap === "insufficient_evidence" && (
          <DisclosureBadge kind="insufficient_evidence" />
        )}
      </div>

      {section.content ? (
        <p className="mt-3 max-w-[720px] whitespace-pre-wrap text-[15px] leading-[1.65]">{section.content}</p>
      ) : gap ? (
        <p className="mt-3 max-w-[720px] text-[14px] italic leading-relaxed text-sub">
          {memoGapCopy(gap)}
        </p>
      ) : (
        <p className="mt-3 max-w-[720px] text-[14px] italic leading-relaxed text-sub">
          Not generated yet — this section has not been written. No claim is made either
          way about the underlying facts.
        </p>
      )}

      {(section.evidence?.length ?? 0) > 0 ? (
        <div className="mt-5">
          <div className="mb-2.5 font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
            Backed by {section.evidence.length} source{section.evidence.length > 1 ? "s" : ""}
          </div>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {(section.evidence ?? []).map((ev: EvidenceRef, i: number) => (
              <EvidenceCard
                key={`${ev.source_locator}-${i}`}
                evidence={ev}
                status={statusFor(ev, section)}
                evidenceCount={1}
              />
            ))}
          </div>
        </div>
      ) : (
        section.content && (
          <div className="mt-4 inline-flex items-center gap-2 rounded-[2px] border border-line bg-raise px-3 py-1.5 font-mono text-[10.5px] text-sub">
            No sources attached — treat as unverified
          </div>
        )
      )}
    </section>
  );
}

/** Contradiction sections mark their sources as contradicted; otherwise confidence decides. */
function statusFor(ev: EvidenceRef, section: MemoSectionDetail): ValidationStatus {
  if (section.content?.startsWith("CONTRADICTION")) return "contradicted";
  if (ev.confidence >= 0.8) return "verified";
  if (ev.confidence >= 0.5) return "weakly_supported";
  return "unknown";
}

export default async function MemoDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const memo = await getMemoDetail(id);
  if (!memo) notFound();

  const filled = memo.sections.filter((s) => s.content != null).length;
  const gaps = memo.sections.filter((s) => !s.content).length;
  const sourceCount = memo.sections.reduce((n, s) => n + (s.evidence?.length ?? 0), 0);
  const approved = memo.status === "funded" || memo.recommendation === "yes";

  return (
    <div className="mx-auto max-w-[1000px] px-10 pb-24 pt-10">
      <Link
        href="/memos"
        className="inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-[0.08em] !text-sub no-underline hover:!text-ink"
      >
        <ArrowLeft className="h-3 w-3" /> All memos
      </Link>

      {/* ---------- header ---------- */}
      <div className="mt-6 border-b border-ink pb-7">
        <div className="mt-3.5 flex flex-wrap items-end justify-between gap-4">
          <h1 className="font-serif text-[48px] font-medium leading-[1.05] tracking-[-0.01em]">
            {memo.company_name}
          </h1>
          <div className="flex flex-wrap items-center gap-2.5 pb-2">
            {memo.source && <DiscoveryChannelBadge channel={memo.source} />}
            {memo.has_contradiction && (
              <span className="rounded-[2px] border border-brand/30 bg-accent px-2 py-1 font-mono text-[10px] uppercase tracking-[0.06em] text-brand-ink">
                Contradiction
              </span>
            )}
            <InvestButton
              opportunityId={memo.opportunity_id}
              alreadyApproved={approved}
            />
          </div>
        </div>
        <div className="mt-2 font-mono text-[12px] text-sub">{memo.founder_name}</div>
        {memo.snapshot && (
          <p className="mt-4 max-w-[720px] text-[15px] leading-relaxed text-sub">{memo.snapshot}</p>
        )}
      </div>

      {/* ---------- meta strip ---------- */}
      <div className="flex flex-wrap items-center gap-8 border-b border-line py-4 font-mono text-[10.5px] uppercase tracking-[0.1em] text-sub">
        <span>
          {filled}/{memo.sections.length} sections filled
        </span>
        <span className={gaps > 0 ? "text-brand-ink" : undefined}>{gaps} gap{gaps === 1 ? "" : "s"} flagged</span>
        <span>{sourceCount} source{sourceCount === 1 ? "" : "s"} cited</span>
        {memo.updated_at && <span className="text-faint">Updated {new Date(memo.updated_at).toLocaleString()}</span>}
        <Link
          href={`/opportunities/${memo.opportunity_id}`}
          className="ml-auto inline-flex items-center gap-1 no-underline"
        >
          Open opportunity <ArrowUpRight className="h-3 w-3" />
        </Link>
      </div>

      {/* ---------- contradiction banner ---------- */}
      {memo.has_contradiction && (
        <div className="mt-6 rounded-[2px] border border-brand/30 bg-accent px-4 py-3 text-[13px] leading-relaxed text-ink">
          <span className="font-semibold text-brand-ink">Validator caught a contradiction.</span> At least one
          claim in this memo conflicts with independently corroborated evidence. The conflicting
          sources are shown side by side in the affected section below.
        </div>
      )}

      {/* ---------- sections ---------- */}
      <div className="mt-2">
        {memo.sections.map((section, i) => (
          <MemoSection key={section.title} section={section} index={i} />
        ))}
      </div>

      <div className="mt-10 border-t border-line pt-6 font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
        No composite scores · Evidence or it didn&apos;t happen
      </div>
    </div>
  );
}
