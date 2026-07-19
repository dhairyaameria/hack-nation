import { DisclosureBadge } from "@/components/ui/ds";
import type { Memo, MemoSection, EvidenceRef } from "@/lib/types";

/**
 * Missing sections are always a visible badge — never hidden
 * (docs/00-OVERVIEW.md §4 rule 3).
 *
 * Renders evidence locators inline when the section carries them. The field is
 * optional so this stays compatible with the shared Memo contract, which has no
 * per-section evidence yet — widening that belongs to Khaled's schema lane.
 */
type SectionWithEvidence = MemoSection & { evidence?: EvidenceRef[] };

export function MemoView({ memo }: { memo: Memo | null | undefined }) {
  if (!memo) {
    return <p className="text-sm italic text-sub">Memo not generated yet.</p>;
  }

  return (
    <div className="divide-y divide-line2">
      {(memo.sections as SectionWithEvidence[]).map((section, i) => (
        <div key={i} className="py-4 first:pt-0 last:pb-0">
          <div className="flex items-center justify-between gap-3">
            <h4 className="font-serif text-[17px] font-semibold">{section.title}</h4>
            {section.not_disclosed && <DisclosureBadge kind="not_disclosed" />}
          </div>

          {/* withheld != not-yet-generated: only claim the founder withheld it
              when not_disclosed actually says so */}
          {section.content ? (
            <p className="mt-1.5 text-[13.5px] leading-relaxed">{section.content}</p>
          ) : section.not_disclosed ? (
            <p className="mt-1.5 text-[13px] italic leading-relaxed text-sub">
              Not disclosed — withheld by the founder, no inference made.
            </p>
          ) : (
            <p className="mt-1.5 text-[13px] italic leading-relaxed text-sub">
              Unavailable at this stage.
            </p>
          )}

          {section.evidence && section.evidence.length > 0 && (
            <div className="mt-2.5 flex flex-wrap gap-2">
              {section.evidence.map((ev, j) => (
                <span
                  key={`${ev.source_locator}-${j}`}
                  className="inline-flex items-center gap-1.5 rounded-[2px] border border-line bg-background px-2 py-1 font-mono text-[10.5px]"
                  title={ev.evidence_snippet}
                >
                  <span className="border-b border-dotted border-dotline-a text-brand-ink">
                    {ev.source_locator}
                  </span>
                  <span className="text-faint">{Math.round(ev.confidence * 100)}%</span>
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
