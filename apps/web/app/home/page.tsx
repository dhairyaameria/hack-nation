import Link from "next/link";
import {
  ArrowRight,
  FileText,
  MessageSquareText,
  Search,
  Settings,
  UploadCloud,
  Users,
  Radar,
} from "lucide-react";
import { getPipelineDashboard } from "@/lib/api/client";
import {
  ConfidenceBadge,
  DiscoveryChannelBadge,
  SectionLabel,
  Sparkline,
  TREND,
  TrustHeatLegend,
  type TrustLevel,
} from "@/components/ui/ds";
import { TrustHeat } from "@/components/ui/trust-heat";
import { formatAxisValue } from "@/components/dashboard/AxisScoreCard";

export const dynamic = "force-dynamic";

/**
 * Landing page. Pipeline rows come from the live API (fixture fallback);
 * the memo / founder / signal tables below are sample rows so the page
 * demos full — they carry a "sample" marker so nothing here reads as a
 * real firm record.
 */

const SAMPLE_MEMOS = [
  { company: "Lumen Yield", founder: "Maya Okafor", filled: 5, total: 5, gaps: 0, updated: "2h ago", contradiction: false },
  { company: "Parseline", founder: "Dana Reeve", filled: 4, total: 5, gaps: 1, updated: "5h ago", contradiction: true },
  { company: "Helio Bench", founder: "Anish Verma", filled: 5, total: 5, gaps: 2, updated: "yesterday", contradiction: false },
  { company: "Notch Robotics", founder: "Kei Tanaka", filled: 3, total: 5, gaps: 2, updated: "2d ago", contradiction: false },
];

const SAMPLE_FOUNDERS: { name: string; company: string; score: number; trend: keyof typeof TREND; spark: number[]; trust: { label: string; level: TrustLevel }[] }[] = [
  { name: "Maya Okafor", company: "Lumen Yield", score: 84, trend: "improving", spark: [0.2, 0.35, 0.3, 0.55, 0.5, 0.7, 0.84], trust: [{ label: "Revenue", level: "trusted" }, { label: "Team", level: "trusted" }, { label: "IP", level: "partial" }, { label: "Traction", level: "trusted" }] },
  { name: "Dr. Anish Verma", company: "Helio Bench", score: 91, trend: "improving", spark: [0.4, 0.5, 0.55, 0.6, 0.75, 0.85, 0.91], trust: [{ label: "Revenue", level: "partial" }, { label: "Team", level: "trusted" }, { label: "IP", level: "trusted" }, { label: "Traction", level: "disputed" }] },
  { name: "Kei Tanaka", company: "Notch Robotics", score: 67, trend: "stable", spark: [0.65, 0.66, 0.68, 0.65, 0.67, 0.66, 0.67], trust: [{ label: "Revenue", level: "partial" }, { label: "Team", level: "trusted" }, { label: "IP", level: "trusted" }, { label: "Traction", level: "partial" }] },
  { name: "Dana Reeve", company: "Parseline", score: 58, trend: "declining", spark: [0.78, 0.74, 0.7, 0.68, 0.62, 0.6, 0.58], trust: [{ label: "Revenue", level: "disputed" }, { label: "Team", level: "trusted" }, { label: "IP", level: "partial" }, { label: "Traction", level: "partial" }] },
];

const SAMPLE_SIGNALS = [
  { founder: "Priya Raman", channel: "github", signal: "Shipped an inference runtime, 1.2k stars in 9 days", stage: "activation-candidate", conf: 0.82, n: 7 },
  { founder: "Tomas Lindqvist", channel: "arxiv", signal: "First author on a cited sparse-attention paper", stage: "scored", conf: 0.64, n: 4 },
  { founder: "Ade Bakare", channel: "hackathon", signal: "Won the ETH Denver hardware track", stage: "outreach-sent", conf: 0.71, n: 5 },
  { founder: "Wei Chen", channel: "producthunt", signal: "#1 of the day, 2.4k upvotes on a dev tool", stage: "discovered", conf: 0.38, n: 2 },
];

const FEATURES = [
  { href: "/apply", icon: UploadCloud, label: "Inbound Sources", body: "Drop a deck. Claims get extracted, screened against the thesis, and every one keeps a pointer back to the slide it came from." },
  { href: "/", icon: Radar, label: "Outbound Sources", body: "Find Lead sweeps GitHub, Hacker News, and arXiv for founders worth a first call, then tracks them through a watchlist state machine." },
  { href: "/memos", icon: FileText, label: "Investment Memos", body: "Company snapshot, hypotheses, SWOT, traction. Gaps stay flagged as gaps — nothing is invented to fill a blank section." },
  { href: "/founders", icon: Users, label: "Founder Book", body: "The founder genome over time: execution velocity, technical depth, resilience, and a network graph you can walk." },
  { href: "/query", icon: Search, label: "NL Query", body: "Ask the pipeline a question in plain English and get an answer with its sources attached." },
  { href: "/agent", icon: MessageSquareText, label: "Agent", body: "Chat that routes to the right skill, compares companies, and cites the evidence behind each claim." },
];

function SampleChip() {
  return (
    <span className="rounded-[2px] border border-line3 bg-line2 px-2 py-[3px] font-mono text-[9.5px] uppercase tracking-[0.06em] text-sub">
      Sample data
    </span>
  );
}

function StatTile({ value, label, sub }: { value: string; label: string; sub?: string }) {
  return (
    <div className="rounded-[2px] border border-line bg-surface p-5">
      <div className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-sub">{label}</div>
      <div className="mt-2 font-serif text-[40px] font-medium leading-none">{value}</div>
      {sub && <div className="mt-1.5 text-[12px] text-sub">{sub}</div>}
    </div>
  );
}

function TableShell({
  title,
  href,
  cta,
  sample,
  children,
}: {
  title: string;
  href: string;
  cta: string;
  sample?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-[2px] border border-line bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-line px-5 py-3">
        <div className="flex items-center gap-2.5">
          <span className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-sub">{title}</span>
          {sample && <SampleChip />}
        </div>
        <Link href={href} className="inline-flex items-center gap-1 font-mono text-[10.5px] uppercase tracking-[0.06em] no-underline">
          {cta} <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
      {children}
    </div>
  );
}

export default async function HomePage() {
  const dashboard = await getPipelineDashboard();
  const opportunities = dashboard.opportunities;
  const needsDecision = opportunities.filter((o) => o.sla?.signal_at && !o.sla?.decision_at);
  const contradictions = opportunities.filter((o) => o.has_contradiction);

  return (
    <div className="mx-auto max-w-[1200px] px-10 pb-24 pt-14">
      {/* ---------- hero ---------- */}
      <div className="border-b border-ink pb-8">
        <SectionLabel className="text-sub">
          VC Brain · {dashboard.active_thesis.name}
        </SectionLabel>
        <h1 className="mt-3.5 font-serif text-[56px] font-medium leading-[1.05] tracking-[-0.01em]">
          Welcome back, VC
        </h1>
        <p className="mt-3 max-w-[620px] text-[15px] leading-relaxed text-sub">
          Every number on this page traces to a source. Three axes, never averaged into one
          score. Where the evidence runs out, you&apos;ll see a gap instead of a guess.
        </p>
      </div>

      {/* ---------- stats ---------- */}
      <div className="mt-8 grid grid-cols-2 gap-5 lg:grid-cols-4">
        <StatTile value={String(opportunities.length)} label="In pipeline" sub="across inbound and outbound" />
        <StatTile value={String(needsDecision.length)} label="Awaiting decision" sub="inside the 24h SLA" />
        <StatTile value={String(contradictions.length)} label="Contradictions" sub="claims that failed validation" />
        <StatTile value={String(SAMPLE_FOUNDERS.length)} label="Founders tracked" sub="genome scored over time" />
      </div>

      {/* ---------- pipeline table (live) ---------- */}
      <div className="mt-14">
        <SectionLabel className="mb-4">Needs your decision</SectionLabel>
        <TableShell title="Pipeline" href="/" cta="Open pipeline">
          {opportunities.length === 0 ? (
            <div className="px-5 py-10 text-center text-[13px] text-sub">
              Nothing in the pipeline yet.{" "}
              <Link href="/apply" className="no-underline">Submit a deck</Link> to get started.
            </div>
          ) : (
            opportunities.map((o) => (
              <Link
                key={o.id}
                href={`/opportunities/${o.id}`}
                className="flex items-center justify-between gap-4 border-b border-line2 px-5 py-4 !text-ink no-underline transition-colors last:border-b-0 hover:bg-raise"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="font-serif text-[17px] font-semibold">{o.company_name}</span>
                    <DiscoveryChannelBadge channel={o.discovery_channel ?? o.source} />
                    {o.has_contradiction && (
                      <span className="rounded-[2px] bg-bad-bg px-[7px] py-[3px] font-mono text-[9.5px] uppercase tracking-[0.06em] text-bad">
                        Contradiction
                      </span>
                    )}
                  </div>
                  <div className="mt-1 font-mono text-[11px] text-sub">{o.founder_name}</div>
                </div>
                <div className="flex shrink-0 items-center gap-5">
                  {o.axis_scores.map((a) => (
                    <div key={a.axis} className="hidden text-right sm:block">
                      <div className="font-mono text-[9px] uppercase tracking-[0.1em] text-sub">
                        {a.axis === "idea_vs_market" ? "Idea⇄Mkt" : a.axis}
                      </div>
                      <div className="font-serif text-[17px] font-semibold capitalize" style={{ color: TREND[a.trend].color }}>
                        {formatAxisValue(a.value)}
                      </div>
                    </div>
                  ))}
                  <ArrowRight className="h-4 w-4 text-faint" />
                </div>
              </Link>
            ))
          )}
        </TableShell>
      </div>

      {/* ---------- memos + signals ---------- */}
      <div className="mt-12 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <TableShell title="Recent memos" href="/memos" cta="All memos" sample>
          {SAMPLE_MEMOS.map((m) => (
            <Link
              key={m.company}
              href="/memos"
              className="flex items-center justify-between gap-3 border-b border-line2 px-5 py-3.5 !text-ink no-underline transition-colors last:border-b-0 hover:bg-raise"
            >
              <div className="min-w-0">
                <div className="text-[14px] font-medium">
                  {m.company} <span className="font-normal text-sub">— {m.founder}</span>
                </div>
                <div className="mt-0.5 font-mono text-[10.5px] text-sub">
                  {m.filled}/{m.total} sections
                  {m.gaps > 0 && <span className="text-warn"> · {m.gaps} gap(s) flagged</span>}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {m.contradiction && (
                  <span className="rounded-[2px] bg-bad-bg px-[7px] py-[3px] font-mono text-[9.5px] uppercase text-bad">
                    Contradiction
                  </span>
                )}
                <span className="font-mono text-[10px] text-faint">{m.updated}</span>
              </div>
            </Link>
          ))}
        </TableShell>

        <TableShell title="Outbound signals" href="/" cta="Find Lead" sample>
          {SAMPLE_SIGNALS.map((s) => (
            <Link
              key={s.founder}
              href="/"
              className="flex items-center justify-between gap-3 border-b border-line2 px-5 py-3.5 !text-ink no-underline transition-colors last:border-b-0 hover:bg-raise"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2.5">
                  <span className="text-[14px] font-medium">{s.founder}</span>
                  <DiscoveryChannelBadge channel={s.channel} />
                </div>
                <div className="mt-1 text-[12px] text-sub">{s.signal}</div>
              </div>
              <div className="shrink-0 text-right">
                <ConfidenceBadge confidence={s.conf} evidenceCount={s.n} />
                <div className="mt-1 font-mono text-[9.5px] uppercase tracking-[0.06em] text-faint">
                  {s.stage}
                </div>
              </div>
            </Link>
          ))}
        </TableShell>
      </div>

      {/* ---------- founder book ---------- */}
      <div className="mt-12">
        <SectionLabel className="mb-4">Founder book</SectionLabel>
        <TableShell title="Genome — 30d trend" href="/founders" cta="Founder book" sample>
          {SAMPLE_FOUNDERS.map((f) => {
            const trend = TREND[f.trend];
            return (
              <Link
                key={f.name}
                href="/founders"
                className="flex items-center justify-between gap-4 border-b border-line2 px-5 py-4 !text-ink no-underline transition-colors last:border-b-0 hover:bg-raise"
              >
                <div className="min-w-0">
                  <div className="text-[14px] font-medium">{f.name}</div>
                  <div className="mt-0.5 font-mono text-[10.5px] text-sub">{f.company}</div>
                </div>
                <div className="flex shrink-0 items-center gap-6">
                  <div className="hidden md:block">
                    <TrustHeat cells={f.trust} size={10} />
                  </div>
                  <Sparkline points={f.spark} stroke={trend.color} width={70} height={22} />
                  <div className="w-[92px] text-right">
                    <span className="font-serif text-[22px] font-semibold">{f.score}</span>
                    <span className="ml-1.5 text-[12px] font-medium" style={{ color: trend.color }}>
                      {trend.arrow} {trend.label}
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </TableShell>
        <div className="mt-3 flex justify-end">
          <TrustHeatLegend />
        </div>
      </div>

      {/* ---------- features ---------- */}
      <div className="mt-14">
        <SectionLabel className="mb-4">Everything in the brain</SectionLabel>
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ href, icon: Icon, label, body }) => (
            <Link
              key={label}
              href={href}
              className="group rounded-[2px] border border-line bg-surface p-5 !text-ink no-underline transition-colors hover:border-ink"
            >
              <div className="flex items-center justify-between">
                <Icon className="h-4 w-4" />
                <ArrowRight className="h-3.5 w-3.5 text-faint transition-colors group-hover:text-ink" />
              </div>
              <div className="mt-3 font-serif text-[19px] font-semibold">{label}</div>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-sub">{body}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* ---------- footer ---------- */}
      <div className="mt-14 flex items-center justify-between border-t border-line pt-6">
        <div className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
          No composite scores · Evidence or it didn&apos;t happen
        </div>
        <Link
          href="/settings/thesis"
          className="inline-flex items-center gap-1.5 rounded-[2px] border border-ink px-3 py-1.5 font-mono text-[11px] !text-ink no-underline hover:bg-raise"
        >
          <Settings className="h-3 w-3" /> Tune thesis
        </Link>
      </div>
    </div>
  );
}
