import { cn } from "@/lib/utils";
import { ConfidenceBadge } from "@/components/ui/ds";
import type { EvidenceRef, ValidationStatus } from "@/lib/types";

const STATUS_STYLE: Record<ValidationStatus, { label: string; color: string; bg: string }> = {
  verified: { label: "Verified", color: "var(--good-ink)", bg: "var(--good-bg)" },
  contradicted: { label: "Contradicted", color: "var(--bad-ink)", bg: "var(--bad-bg)" },
  weakly_supported: { label: "Weakly supported", color: "var(--warn-ink)", bg: "var(--warn-bg)" },
  unknown: { label: "Unknown", color: "var(--sub)", bg: "var(--line2)" },
};

export function EvidenceStatusTag({ status }: { status: ValidationStatus }) {
  const s = STATUS_STYLE[status];
  return (
    <span
      className="whitespace-nowrap rounded-[2px] px-[7px] py-[3px] font-mono text-[9.5px] uppercase tracking-[0.06em]"
      style={{ color: s.color, background: s.bg }}
    >
      {s.label}
    </span>
  );
}

/**
 * Every claim traces to a source — evidence is first-class.
 * Compact by default; pass `quote`/`trace` for the expanded state.
 */
export function EvidenceCard({
  evidence,
  status,
  evidenceCount = 1,
  quote,
  trace,
  href,
  className,
}: {
  evidence: EvidenceRef;
  status: ValidationStatus;
  evidenceCount?: number;
  quote?: string;
  trace?: string;
  href?: string;
  className?: string;
}) {
  const expanded = Boolean(quote || trace);
  return (
    <div
      className={cn(
        "rounded-[2px] border bg-surface p-4 transition-all",
        expanded
          ? "border-brand shadow-[0_2px_12px_rgba(25,23,19,0.08)]"
          : "cursor-pointer border-line hover:-translate-y-px hover:border-brand hover:shadow-[0_2px_10px_rgba(25,23,19,0.07)]",
        className
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[11px] text-brand-ink">
          <span className="border-b border-dotted border-dotline-a pb-px">
            {evidence.source_locator}
          </span>
        </span>
        <EvidenceStatusTag status={status} />
      </div>
      <p className="my-2.5 text-[12.5px] leading-relaxed text-ink">{evidence.evidence_snippet}</p>
      {quote && (
        <blockquote className="mb-3 border-l-2 border-brand bg-background px-3.5 py-2.5 font-serif text-[15px] italic leading-snug">
          “{quote}”
        </blockquote>
      )}
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-line2 pt-2.5">
        <ConfidenceBadge confidence={evidence.confidence} evidenceCount={evidenceCount} />
        {trace ? (
          <span className="font-mono text-[10.5px] text-sub">TRACE&nbsp; {trace}</span>
        ) : (
          <span className="font-mono text-[10px] uppercase text-faint">{evidence.source_type}</span>
        )}
        {href && (
          <a
            href={href}
            className="rounded-[2px] border border-ink px-3 py-1 font-mono text-[11px] !text-ink no-underline hover:bg-raise"
          >
            Open source ↗
          </a>
        )}
      </div>
    </div>
  );
}
