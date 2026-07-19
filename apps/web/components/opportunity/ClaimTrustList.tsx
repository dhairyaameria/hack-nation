"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { ExternalLink } from "@/components/ui/ExternalLink";
import { cn } from "@/lib/utils";
import type { ClaimTrust, EvidenceRef, ValidationStatus } from "@/lib/types";

const STATUS_STYLE: Record<ValidationStatus, string> = {
  verified: "text-[var(--good-ink)] bg-[var(--good-bg)]",
  contradicted: "text-[var(--bad-ink)] bg-[var(--bad-bg)]",
  weakly_supported: "text-[var(--warn-ink)] bg-[var(--warn-bg)]",
  unknown: "text-sub bg-muted",
};

const STATUS_LABEL: Record<ValidationStatus, string> = {
  verified: "Verified",
  contradicted: "Contradicted",
  weakly_supported: "Weak",
  unknown: "Unconfirmed",
};

type SourceEntry = {
  id: number;
  href: string | null;
  host: string;
  snippet: string;
  sourceType: string;
  confidence: number;
};

function isHttpUrl(value: string | undefined | null): value is string {
  return !!value && /^https?:\/\//i.test(value);
}

function hostLabel(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function shortLabel(ev: EvidenceRef): string {
  if (isHttpUrl(ev.source_locator)) return hostLabel(ev.source_locator);
  if (ev.source_type === "outbound_research") return "Research dossier";
  if (ev.source_type === "deck") return ev.source_locator || "Deck";
  return (ev.source_type || "Source").replace(/_/g, " ");
}

function sourceKey(ev: EvidenceRef): string {
  const loc = ev.source_locator || "";
  // Dedupe web hits by URL; keep research/deck rows distinct by snippet head.
  if (isHttpUrl(loc)) return `url::${loc}`;
  return `${ev.source_type}::${loc}::${(ev.evidence_snippet || "").slice(0, 60)}`;
}

function buildIndex(claims: ClaimTrust[]): {
  sources: SourceEntry[];
  citesByClaim: Record<string, number[]>;
} {
  const keyToId = new Map<string, number>();
  const sources: SourceEntry[] = [];
  const citesByClaim: Record<string, number[]> = {};

  for (const claim of claims) {
    const cites: number[] = [];
    for (const ev of claim.evidence || []) {
      const key = sourceKey(ev);
      let id = keyToId.get(key);
      if (id == null) {
        id = sources.length + 1;
        keyToId.set(key, id);
        const href = isHttpUrl(ev.source_locator) ? ev.source_locator : null;
        sources.push({
          id,
          href,
          host: shortLabel(ev),
          snippet: (ev.evidence_snippet || "").trim(),
          sourceType: ev.source_type,
          confidence: ev.confidence ?? 0.5,
        });
      }
      if (!cites.includes(id)) cites.push(id);
    }
    citesByClaim[claim.claim_id] = cites;
  }

  return { sources, citesByClaim };
}

function CitationChip({
  n,
  onActivate,
  active,
}: {
  n: number;
  onActivate: (n: number) => void;
  active: boolean;
}) {
  return (
    <button
      type="button"
      onClick={() => onActivate(n)}
      className={cn(
        "mx-0.5 inline-flex h-4 min-w-4 translate-y-[-1px] items-center justify-center rounded-[2px] px-1 font-mono text-[10px] transition-colors",
        active
          ? "bg-ink text-background"
          : "bg-muted text-sub hover:bg-ink hover:text-background"
      )}
      aria-label={`Jump to source ${n}`}
    >
      {n}
    </button>
  );
}

/**
 * User-facing evidence analysis: one readable paragraph with inline citations,
 * a clean source trace, and a compact verification ledger (not a wall of cards).
 */
export function ClaimTrustList({ claims }: { claims: ClaimTrust[] }) {
  const [activeCite, setActiveCite] = useState<number | null>(null);
  const [ledgerOpen, setLedgerOpen] = useState(false);
  const [expandedSource, setExpandedSource] = useState<number | null>(null);

  const { sources, citesByClaim } = useMemo(() => buildIndex(claims), [claims]);

  const verified = claims.filter((c) => c.validation_status === "verified").length;
  const contradicted = claims.filter((c) => c.validation_status === "contradicted").length;
  const avgTrust =
    claims.length === 0
      ? 0
      : claims.reduce((sum, c) => sum + (c.trust_score ?? 0), 0) / claims.length;

  if (claims.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">
        No evidence analysis yet — run Analyze to gather public sources and draft claims.
      </p>
    );
  }

  function jumpTo(n: number) {
    setActiveCite(n);
    setExpandedSource(n);
    document.getElementById(`cite-${n}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[11px] text-sub">
        <span>
          Trust <span className="text-ink">{Math.round(avgTrust * 100)}</span>/100 avg
        </span>
        <span>
          <span className="text-[var(--good-ink)]">{verified}</span> verified
        </span>
        {contradicted > 0 && (
          <span>
            <span className="text-[var(--bad-ink)]">{contradicted}</span> contradicted
          </span>
        )}
        <span>{sources.length} sources</span>
      </div>

      <div className="rounded-[2px] border border-line bg-surface px-5 py-4">
        <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.12em] text-sub">
          Evidence analysis
        </p>
        <p className="text-[15px] leading-[1.75] text-ink">
          {claims.map((claim, i) => {
            const text = claim.text.replace(/\s+/g, " ").trim();
            const cites = citesByClaim[claim.claim_id] || [];
            const needsPeriod = !/[.!?]$/.test(text);
            return (
              <span key={claim.claim_id}>
                {i > 0 ? " " : null}
                <span
                  className={cn(
                    claim.validation_status === "contradicted" &&
                      "underline decoration-dotted decoration-[var(--bad-ink)]",
                    claim.validation_status === "unknown" && "text-ink/85"
                  )}
                >
                  {text}
                  {needsPeriod ? "." : ""}
                </span>
                {cites.map((n) => (
                  <CitationChip
                    key={`${claim.claim_id}-${n}`}
                    n={n}
                    active={activeCite === n}
                    onActivate={jumpTo}
                  />
                ))}
              </span>
            );
          })}
        </p>
        {contradicted > 0 && (
          <p className="mt-3 border-t border-line2 pt-3 text-xs text-[var(--bad-ink)]">
            Dotted underline marks claims the validator contradicted — treat as disputed, not fact.
          </p>
        )}
      </div>

      <div className="space-y-2">
        <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-sub">Sources</p>
        <ol className="divide-y divide-line2 rounded-[2px] border border-line bg-surface">
          {sources.map((s) => {
            const open = expandedSource === s.id;
            return (
              <li
                key={s.id}
                id={`cite-${s.id}`}
                className={cn("px-4 py-3 transition-colors", activeCite === s.id && "bg-raise")}
              >
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-[2px] bg-muted font-mono text-[11px] text-ink">
                    {s.id}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                      {s.href ? (
                        <ExternalLink
                          href={s.href}
                          className="truncate text-sm font-medium text-ink hover:underline"
                        >
                          {s.host}
                        </ExternalLink>
                      ) : (
                        <span className="text-sm font-medium text-ink">{s.host}</span>
                      )}
                      <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-sub">
                        {s.sourceType.replace(/_/g, " ")}
                      </span>
                      <span className="font-mono text-[10px] text-sub">
                        {Math.round(s.confidence * 100)}% conf.
                      </span>
                    </div>
                    {s.snippet && (
                      <button
                        type="button"
                        onClick={() => setExpandedSource(open ? null : s.id)}
                        className="mt-1 w-full text-left text-[13px] leading-relaxed text-sub"
                      >
                        <span className={cn(!open && "line-clamp-2")}>{s.snippet}</span>
                        <span className="ml-1 font-mono text-[10px] text-ink/50">
                          {open ? "less" : "more"}
                        </span>
                      </button>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </div>

      <div className="rounded-[2px] border border-line">
        <button
          type="button"
          onClick={() => setLedgerOpen((v) => !v)}
          className="flex w-full items-center justify-between px-4 py-3 text-left"
        >
          <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-sub">
            Verification ledger · {claims.length} claims
          </span>
          {ledgerOpen ? (
            <ChevronDown className="h-3.5 w-3.5 text-sub" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 text-sub" />
          )}
        </button>
        {ledgerOpen && (
          <ul className="space-y-2.5 border-t border-line2 px-4 py-3">
            {claims.map((claim) => (
              <li key={claim.claim_id} className="flex items-start justify-between gap-3">
                <p className="text-[13px] leading-snug text-ink/90">{claim.text}</p>
                <div className="flex shrink-0 flex-col items-end gap-1">
                  <span
                    className={cn(
                      "rounded-[2px] px-1.5 py-0.5 font-mono text-[9.5px] uppercase tracking-[0.06em]",
                      STATUS_STYLE[claim.validation_status]
                    )}
                  >
                    {STATUS_LABEL[claim.validation_status]}
                  </span>
                  <span className="font-mono text-[10px] text-sub">
                    {Math.round((claim.trust_score ?? 0) * 100)}/100
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
