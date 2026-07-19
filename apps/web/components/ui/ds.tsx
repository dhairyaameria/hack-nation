/**
 * VC Brain design-system primitives (design doc: "VC Brain Components.dc.html").
 * Tokens live in app/globals.css. Rules: three axes never composited,
 * confidence always shown with evidence count, withheld ≠ unverifiable.
 * Server-safe on purpose — TREND etc. are consumed as data by server
 * components. The stateful TrustHeat lives in trust-heat.tsx ("use client").
 */

import type { ReactNode } from "react";
import {
  ArrowDownToLine,
  CircleUser,
  FileText,
  GitBranch,
  Radar,
  Rocket,
  Share2,
  Users,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ValidationStatus } from "@/lib/types";

/* ---------- SectionLabel ---------- */

export function SectionLabel({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-ink",
        className
      )}
    >
      <span className="inline-block h-2 w-2 bg-brand" />
      <span>{children}</span>
    </div>
  );
}

/* ---------- Sparkline ---------- */

export function Sparkline({
  points,
  stroke = "var(--sub)",
  width = 86,
  height = 26,
}: {
  points: number[]; // 0..1, oldest first
  stroke?: string;
  width?: number;
  height?: number;
}) {
  if (points.length < 2) return null;
  const pts = points
    .map((v, i) => {
      const x = 2 + (i * (width - 4)) / (points.length - 1);
      const y = 2 + (1 - Math.min(1, Math.max(0, v))) * (height - 4);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden>
      <polyline points={pts} fill="none" stroke={stroke} strokeWidth="1.6" />
    </svg>
  );
}

/* ---------- Trend ---------- */

export const TREND = {
  improving: { arrow: "↗", label: "Improving", color: "var(--good-ink)" },
  stable: { arrow: "→", label: "Stable", color: "var(--sub)" },
  declining: { arrow: "↘", label: "Declining", color: "var(--bad-ink)" },
} as const;

/* ---------- ConfidenceBadge ---------- */

export function confidenceLevel(confidence: number): "High" | "Medium" | "Low" {
  return confidence >= 0.75 ? "High" : confidence >= 0.4 ? "Medium" : "Low";
}

const CONF_DOT = {
  High: "var(--good-ink)",
  Medium: "var(--warn-dot)",
  Low: "var(--bad-ink)",
};

/** Always level + evidence count — never a bare number. */
export function ConfidenceBadge({
  confidence,
  evidenceCount,
  className,
}: {
  confidence: number;
  evidenceCount: number;
  className?: string;
}) {
  const level = confidenceLevel(confidence);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-[2px] border border-line px-2 py-1 font-mono text-[11px] text-ink",
        className
      )}
    >
      <span
        className="inline-block h-[7px] w-[7px] rounded-full"
        style={{ background: CONF_DOT[level] }}
      />
      {level} · {evidenceCount} evid.
    </span>
  );
}

/* ---------- TrustHeat ---------- */

export type TrustLevel = "trusted" | "partial" | "disputed";

export const TRUST_COLOR: Record<TrustLevel, string> = {
  trusted: "#2c3630",
  partial: "#8a928c",
  disputed: "#0a0a0b",
};

export function trustLevelFromStatus(status: ValidationStatus): TrustLevel {
  if (status === "verified") return "trusted";
  if (status === "contradicted") return "disputed";
  return "partial";
}

export function TrustHeatLegend() {
  return (
    <div className="flex gap-3.5 font-mono text-[10px] text-sub">
      {(["trusted", "partial", "disputed"] as const).map((l) => (
        <span key={l} className="inline-flex items-center gap-1.5 uppercase">
          <span className="h-2 w-2 rounded-[2px]" style={{ background: TRUST_COLOR[l] }} />
          {l}
        </span>
      ))}
    </div>
  );
}

/* ---------- DiscoveryChannelBadge ---------- */

const CHANNEL_ICON: Record<string, typeof Radar> = {
  inbound: ArrowDownToLine,
  direct_apply: ArrowDownToLine,
  github: GitBranch,
  hackathon: Zap,
  arxiv: FileText,
  linkedin: CircleUser,
  producthunt: Rocket,
  referral: Users,
  network_proximity: Share2,
};

export function DiscoveryChannelBadge({ channel, className }: { channel: string; className?: string }) {
  const Icon = CHANNEL_ICON[channel.toLowerCase()] ?? Radar;
  const label = channel.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-[2px] border border-line bg-background px-2 py-[3px] font-mono text-[10.5px] text-ink transition-colors hover:border-ink",
        className
      )}
    >
      <Icon className="h-3 w-3" />
      {label}
    </span>
  );
}

/* ---------- DisclosureBadge: NotDisclosed vs Unknown ---------- */

/** Withheld ≠ unverifiable — grey is a fact, amber is a gap. */
export function DisclosureBadge({ kind }: { kind: "not_disclosed" | "unknown" }) {
  if (kind === "not_disclosed") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-[2px] border border-line3 bg-line2 px-2.5 py-1 font-mono text-[11px] text-sub">
        <span className="font-semibold">—</span>Not disclosed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-[2px] border border-brand/25 bg-accent px-2.5 py-1 font-mono text-[11px] text-brand-ink">
      <span className="font-semibold">?</span>Unknown — low confidence
    </span>
  );
}
