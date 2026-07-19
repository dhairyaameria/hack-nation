import type { AxisScore, OpportunitySummary } from "@/lib/types";
import { AxisScoreCard } from "@/components/dashboard/AxisScoreCard";
import { OpportunityCard } from "@/components/dashboard/OpportunityCard";
import { EvidenceCard } from "@/components/opportunity/EvidenceCard";
import {
  ConfidenceBadge,
  DisclosureBadge,
  DiscoveryChannelBadge,
  SectionLabel,
  TrustHeatLegend,
} from "@/components/ui/ds";
import { TrustHeat } from "@/components/ui/trust-heat";

/**
 * Component library showcase — implements "VC Brain Components.dc.html".
 * Sample data mirrors the design doc; nothing here hits the API.
 */

const ev = (
  source_type: string,
  source_locator: string,
  evidence_snippet: string,
  confidence: number
) => ({ source_type, source_locator, evidence_snippet, confidence });

const AXES: { score: AxisScore; history: number[] }[] = [
  {
    score: {
      axis: "founder",
      value: 0.84,
      trend: "improving",
      confidence: 0.88,
      evidence: [
        ev("filing", "SEC EDGAR", "2× prior exit — verified via filings", 0.9),
        ev("github", "repo activity", "312 commits / last 90 days", 0.85),
        ev("call", "Ref call 03", "“relentless, precise”", 0.7),
      ],
    },
    history: [0.2, 0.35, 0.3, 0.55, 0.5, 0.7, 0.84],
  },
  {
    score: {
      axis: "market",
      value: 0.61,
      trend: "stable",
      confidence: 0.55,
      evidence: [
        ev("web", "2 sources", "TAM claim contradicted by 2 sources", 0.4),
        ev("web", "Crunchbase", "3 incumbent raises this quarter", 0.6),
      ],
    },
    history: [0.58, 0.55, 0.6, 0.55, 0.58, 0.55, 0.61],
  },
  {
    score: {
      axis: "idea_vs_market",
      value: 0.72,
      trend: "improving",
      confidence: 0.62,
      evidence: [
        ev("call", "Buyer interviews", "Wedge matches buyer interviews 4/5", 0.7),
        ev("deck", "Pilot 01", "Pricing thesis untested — 1 pilot", 0.4),
      ],
    },
    history: [0.15, 0.4, 0.3, 0.5, 0.48, 0.65, 0.72],
  },
];

const EVIDENCE = [
  {
    e: ev("deck", "Slide 7", "Claims $1.2M ARR as of March; chart shows 22% MoM growth.", 0.9),
    status: "verified" as const,
    count: 9,
  },
  {
    e: ev("github", "commit a3f21c", "Core inference engine rewritten solo by founder over 11 days.", 0.85),
    status: "verified" as const,
    count: 6,
  },
  {
    e: ev("article", "techledger.io", "“Raised a $2M pre-seed” — no filing found to corroborate.", 0.25),
    status: "contradicted" as const,
    count: 2,
  },
  {
    e: ev("call", "Call 02 · 14:32", "Founder states 3 pilot LOIs; two named, one withheld.", 0.55),
    status: "weakly_supported" as const,
    count: 4,
  },
];

const HEAT_CELLS = [
  { label: "Revenue claims", level: "trusted" as const },
  { label: "Team background", level: "trusted" as const },
  { label: "Technical IP", level: "partial" as const },
  { label: "Market sizing", level: "disputed" as const },
  { label: "Traction", level: "partial" as const },
  { label: "Regulatory", level: "trusted" as const },
];

const CHANNELS = ["inbound", "github", "hackathon", "arxiv", "producthunt", "referral"];

const hoursAgo = (h: number) => new Date(Date.now() - h * 3_600_000).toISOString();

const OPPS: OpportunitySummary[] = [
  {
    id: "demo-lumen",
    company_name: "Lumen Yield",
    founder_name: "Maya Okafor — solo, technical",
    founder_id: "demo",
    source: "outbound",
    discovery_channel: "github",
    triggering_signal: "Grid-scale battery analytics for merchant power traders.",
    thesis_fit_score: 0.91,
    status: "diligence",
    has_contradiction: false,
    axis_scores: [
      { axis: "founder", value: 0.84, trend: "improving", confidence: 0.88, evidence: [] },
      { axis: "market", value: 0.61, trend: "stable", confidence: 0.55, evidence: [] },
      { axis: "idea_vs_market", value: 0.72, trend: "improving", confidence: 0.62, evidence: [] },
    ],
    sla: { signal_at: hoursAgo(24 - 14.4), screening_at: null, diligence_at: null, decision_at: null },
  },
  {
    id: "demo-parseline",
    company_name: "Parseline",
    founder_name: "Dana Reeve & Tom Iqbal — 2nd-time team",
    founder_id: "demo",
    source: "inbound",
    discovery_channel: "inbound",
    triggering_signal: "Contract-to-cashflow parsing for mid-market CFOs.",
    thesis_fit_score: 0.66,
    status: "screening",
    has_contradiction: true,
    axis_scores: [
      { axis: "founder", value: 0.58, trend: "declining", confidence: 0.6, evidence: [] },
      { axis: "market", value: 0.79, trend: "improving", confidence: 0.8, evidence: [] },
      { axis: "idea_vs_market", value: 0.66, trend: "stable", confidence: 0.55, evidence: [] },
    ],
    sla: { signal_at: hoursAgo(24 - 6.2), screening_at: null, diligence_at: null, decision_at: null },
  },
  {
    id: "demo-helio",
    company_name: "Helio Bench",
    founder_name: "Dr. Anish Verma — PhD, first-time",
    founder_id: "demo",
    source: "outbound",
    discovery_channel: "arxiv",
    triggering_signal: "Autonomous lab notebooks for materials science.",
    thesis_fit_score: 0.7,
    status: "screening",
    has_contradiction: false,
    axis_scores: [
      { axis: "founder", value: 0.91, trend: "improving", confidence: 0.9, evidence: [] },
      { axis: "market", value: 0.44, trend: "declining", confidence: 0.5, evidence: [] },
      { axis: "idea_vs_market", value: 0.7, trend: "improving", confidence: 0.65, evidence: [] },
    ],
    sla: { signal_at: hoursAgo(-28), screening_at: null, diligence_at: null, decision_at: null },
  },
];

function Section({ n, title, note }: { n: string; title: string; note?: string }) {
  return (
    <div className="mt-14 mb-5 flex items-baseline justify-between">
      <SectionLabel>
        {n} — {title}
      </SectionLabel>
      {note && <div className="font-mono text-[11px] text-brand-ink">⌁ {note}</div>}
    </div>
  );
}

export default function DesignPage() {
  return (
    <div className="mx-auto max-w-[1200px] px-10 pb-24 pt-14">
      {/* header + tokens */}
      <div className="flex flex-wrap items-end justify-between gap-6 border-b border-ink pb-7">
        <div>
          <SectionLabel className="text-sub">VC Brain · Component Library · v0.1</SectionLabel>
          <h1 className="mt-3.5 font-serif text-[56px] font-medium leading-[1.05] tracking-[-0.01em]">
            Evidence-first
            <br />
            components
          </h1>
        </div>
        <p className="m-0 max-w-[380px] text-right text-sm leading-relaxed text-sub">
          One token system for sourcing, scoring, and deciding. Notion-approachable,
          Bloomberg-dense. Three axes, never one number.
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-10 border-b border-line py-4">
        <div className="flex items-center gap-1.5">
          {["var(--background)", "var(--surface)", "var(--ink)", "var(--brand)", "var(--good-ink)", "var(--warn-dot)", "var(--bad-ink)"].map(
            (c) => (
              <div key={c} className="h-[26px] w-[26px] border border-line" style={{ background: c }} />
            )
          )}
        </div>
        <div className="font-serif text-xl">
          Newsreader <span className="text-faint">/ display</span>
        </div>
        <div className="text-sm">
          Helvetica <span className="text-faint">/ ui</span>
        </div>
        <div className="font-mono text-xs">
          IBM Plex Mono <span className="text-faint">/ data</span>
        </div>
        <div className="font-mono text-[11px] text-sub">
          SPACE 4·8·12·20·32 &nbsp; RADIUS 2 &nbsp; BORDER 1PX LINE TOKEN
        </div>
      </div>

      <Section n="01" title="AxisScoreCard" note="three independent axes — never averaged, never composited" />
      <div className="grid grid-cols-3 gap-5">
        {AXES.map(({ score, history }) => (
          <AxisScoreCard key={score.axis} score={score} history={history} />
        ))}
      </div>

      <Section n="02" title="EvidenceCard" note="every claim traces to a source — evidence is first-class" />
      <div className="grid grid-cols-4 gap-4">
        {EVIDENCE.map(({ e, status, count }) => (
          <EvidenceCard key={e.source_locator} evidence={e} status={status} evidenceCount={count} />
        ))}
      </div>
      <div className="mt-4 grid grid-cols-[1fr_3fr] items-start gap-4">
        <div className="pt-1 font-mono text-[10px] tracking-[0.1em] text-faint">
          ↳ HOVER / EXPANDED STATE
        </div>
        <EvidenceCard
          evidence={ev("deck", "Slide 7", "Claims $1.2M ARR as of March 2026; chart shows 22% MoM growth over trailing six months.", 0.9)}
          status="verified"
          evidenceCount={9}
          quote="We crossed $1.2M ARR in March, growing 22% month over month since October."
          trace="Deck v3 → Slide 7 → claim #12 → cross-checked: Stripe export, ref call 02"
          href="#"
        />
      </div>

      <div className="mt-14 grid grid-cols-2 gap-5">
        <div className="rounded-[2px] border border-line bg-surface p-5">
          <SectionLabel className="mb-4">03 — ConfidenceBadge</SectionLabel>
          <div className="flex flex-wrap gap-2.5">
            <ConfidenceBadge confidence={0.9} evidenceCount={12} />
            <ConfidenceBadge confidence={0.55} evidenceCount={5} />
            <ConfidenceBadge confidence={0.2} evidenceCount={2} />
          </div>
          <div className="mt-4 font-mono text-[11px] text-brand-ink">
            ⌁ always level + evidence count — never a bare number
          </div>
        </div>

        <div className="rounded-[2px] border border-line bg-surface p-5">
          <SectionLabel className="mb-4">04 — TrustHeatCell</SectionLabel>
          <TrustHeat cells={HEAT_CELLS} size={22} withTip />
          <div className="mt-4">
            <TrustHeatLegend />
          </div>
        </div>

        <div className="rounded-[2px] border border-line bg-surface p-5">
          <SectionLabel className="mb-4">05 — DiscoveryChannelBadge</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {CHANNELS.map((c) => (
              <DiscoveryChannelBadge key={c} channel={c} />
            ))}
          </div>
        </div>

        <div className="rounded-[2px] border border-line bg-surface p-5">
          <SectionLabel className="mb-4">06 — NotDisclosed vs Unknown</SectionLabel>
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3">
              <DisclosureBadge kind="not_disclosed" />
              <span className="text-[11.5px] text-sub">founder withheld the data · no inference made</span>
            </div>
            <div className="flex items-center gap-3">
              <DisclosureBadge kind="unknown" />
              <span className="text-[11.5px] text-sub">system searched and could not confirm</span>
            </div>
          </div>
          <div className="mt-4 font-mono text-[11px] text-brand-ink">
            ⌁ withheld ≠ unverifiable — grey is a fact, amber is a gap
          </div>
        </div>
      </div>

      <Section n="07" title="OpportunityCard · pipeline list" />
      <div className="rounded-[2px] border border-line bg-surface">
        <div className="flex items-center justify-between border-b border-line px-5 py-3 font-mono text-[10.5px] uppercase tracking-[0.1em] text-sub">
          <span>Pipeline — needs decision</span>
          <span>{OPPS.length} open · sorted by SLA</span>
        </div>
        {OPPS.map((o) => (
          <OpportunityCard key={o.id} opp={o} />
        ))}
      </div>

      <div className="mt-7 flex justify-between font-mono text-[10.5px] text-faint">
        <span>VC BRAIN DS · 01–07</span>
        <span>NO COMPOSITE SCORES · EVIDENCE OR IT DIDN&apos;T HAPPEN</span>
      </div>
    </div>
  );
}
