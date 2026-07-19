/**
 * Thin fetch wrapper for the FastAPI backend, with fixture fallback so the
 * dashboard is demoable before every real endpoint lands (Wave 1 → Wave 2
 * cutover). See `docs/15-MOCK-FIXTURES.md`.
 */

// Local copies of shared/fixtures/*.json — Turbopack cannot bundle JSON
// imports from outside the app's project root, so these are synced copies,
// not a separate source of truth. Keep in sync per docs/15-MOCK-FIXTURES.md §6.
import pipelineFixture from "@/lib/fixtures/pipeline-dashboard.json";
import opportunityFixture from "@/lib/fixtures/opportunity-detail.json";
import founderFixture from "@/lib/fixtures/founder-profile.json";
import thesisFixture from "@/lib/fixtures/thesis-active.json";
import networkGraphFixture from "@/lib/fixtures/network-graph-seed.json";
import memosFixture from "@/lib/fixtures/memos.json";
import type { OpportunityDetail, OpportunitySummary } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USE_FIXTURES = process.env.NEXT_PUBLIC_USE_FIXTURES === "true";

interface PipelineDashboard {
  active_thesis: { id: string; name: string };
  opportunities: OpportunitySummary[];
}

async function tryFetch<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function getPipelineDashboard(): Promise<PipelineDashboard> {
  if (!USE_FIXTURES) {
    const live = await tryFetch<PipelineDashboard>("/api/v1/opportunities");
    if (live) return live;
  }
  return pipelineFixture as PipelineDashboard;
}

export async function getOpportunityDetail(id: string): Promise<OpportunityDetail | null> {
  if (!USE_FIXTURES) {
    const live = await tryFetch<OpportunityDetail>(`/api/v1/opportunity/${id}`);
    if (live) return live;
  }
  // Fixture only has full detail for opp-contradiction; fall back to the
  // dashboard summary for everything else so every card is clickable.
  if (id === opportunityFixture.id) return opportunityFixture as OpportunityDetail;
  const dashboard = await getPipelineDashboard();
  const summary = dashboard.opportunities.find((o) => o.id === id);
  return summary ? { ...summary, claims: [], memo: null, trace_id: null } : null;
}

export async function getFounderProfile(id: string) {
  if (!USE_FIXTURES) {
    const live = await tryFetch<typeof founderFixture>(`/api/v1/founders/${id}`);
    if (live) return live;
  }
  return founderFixture.id === id ? founderFixture : null;
}

export async function getActiveThesis() {
  if (!USE_FIXTURES) {
    const live = await tryFetch<typeof thesisFixture>("/api/v1/thesis/active");
    if (live) return live;
  }
  return thesisFixture;
}

export async function getNetworkGraphSeed(founderId: string) {
  if (!USE_FIXTURES) {
    const live = await tryFetch<Record<string, unknown>>(`/api/v1/founders/${founderId}/network`);
    if (live) return live;
  }
  return (networkGraphFixture as Record<string, unknown>)[founderId] ?? null;
}

export interface DedupeInfo {
  action: "attached" | "created";
  reason?: string;
  prior_status?: string | null;
  prior_source?: string | null;
  deferred?: string[];
}

export interface SubmitApplicationResult {
  opportunity_id: string;
  company_id?: string | null;
  company_name: string;
  deck_filename: string | null;
  has_deck?: boolean;
  deck_url?: string | null;
  claims_extracted: number;
  screen_verdict: "pass" | "reject" | "needs-more-info";
  screen_reason: string;
  dedupe?: DedupeInfo;
}

export interface InboundApplication {
  id: string;
  company_id?: string | null;
  company_name: string;
  company_sector?: string | null;
  company_stage?: string | null;
  founder_name: string;
  founder_id?: string;
  source: string;
  screen_verdict?: string | null;
  thesis_fit_score?: number | null;
  status?: string;
  has_deck?: boolean;
  deck_filename?: string | null;
  deck_url?: string | null;
  has_contradiction?: boolean;
}

export interface CompanyProfile {
  id: string;
  name: string;
  domain?: string | null;
  sector?: string | null;
  stage?: string | null;
  description?: string | null;
  enrichment?: {
    summary?: string;
    citations?: string[];
    web_results?: { title?: string; url?: string; snippet?: string }[];
    disclaimer?: string;
    sources?: string[];
  };
  opportunities?: InboundApplication[];
  primary_opportunity_id?: string | null;
  deck_url?: string | null;
  has_deck?: boolean;
  deck_filename?: string | null;
}

export function deckAbsoluteUrl(deckUrl: string | null | undefined): string | null {
  if (!deckUrl) return null;
  if (deckUrl.startsWith("http")) return deckUrl;
  return `${API_URL}${deckUrl}`;
}

export async function getInboundApplications(): Promise<InboundApplication[]> {
  if (!USE_FIXTURES) {
    const live = await tryFetch<{ applications: InboundApplication[] }>("/api/v1/inbound/applications");
    if (live) return live.applications;
  }
  const dash = await getPipelineDashboard();
  return dash.opportunities.filter((o) => o.source === "inbound") as InboundApplication[];
}

export async function getCompanyProfile(companyId: string): Promise<CompanyProfile | null> {
  if (!USE_FIXTURES) {
    return tryFetch<CompanyProfile>(`/api/v1/companies/${companyId}`);
  }
  return null;
}

export async function submitApplication(formData: FormData): Promise<SubmitApplicationResult> {
  const res = await fetch(`${API_URL}/api/v1/application/submit`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Submission failed (${res.status})`);
  return res.json();
}

export async function analyzeOpportunity(id: string): Promise<unknown> {
  const res = await fetch(`${API_URL}/api/v1/opportunity/${id}/analyze`, { method: "POST" });
  if (!res.ok) throw new Error(`Analysis failed (${res.status})`);
  return res.json();
}

export interface MemoListItem {
  id: string;
  opportunity_id: string;
  company_name: string;
  founder_name: string;
  source?: string | null;
  status?: string | null;
  recommendation?: string | null;
  decision_at?: string | null;
  has_contradiction: boolean;
  section_count: number;
  sections_filled: number;
  gaps_flagged: number;
  snapshot?: string | null;
  updated_at?: string | null;
  created_at?: string | null;
}

/** A memo section with its supporting evidence. */
export interface MemoSectionDetail {
  title: string;
  content: string | null;
  not_disclosed: boolean;
  required?: boolean;
  evidence: EvidenceRef[];
}

export interface MemoDetail {
  id: string;
  opportunity_id: string;
  company_name: string;
  founder_name: string;
  source?: string | null;
  status?: string | null;
  recommendation?: string | null;
  has_contradiction: boolean;
  snapshot?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  sections: MemoSectionDetail[];
}

const memoFixtures = memosFixture.memos as MemoDetail[];

/** List counts are derived, never stored — they cannot drift from the sections. */
function toListItem(m: MemoDetail): MemoListItem {
  return {
    id: m.id,
    opportunity_id: m.opportunity_id,
    company_name: m.company_name,
    founder_name: m.founder_name,
    source: m.source,
    status: m.status,
    recommendation: m.recommendation,
    has_contradiction: m.has_contradiction,
    snapshot: m.snapshot,
    created_at: m.created_at,
    updated_at: m.updated_at,
    section_count: m.sections.length,
    sections_filled: m.sections.filter((s) => s.content != null).length,
    gaps_flagged: m.sections.filter((s) => s.not_disclosed).length,
  };
}

export async function decideOpportunity(
  id: string,
  body: { recommendation?: "yes" | "no" | "needs-more-info"; confidence?: number } = {},
): Promise<{ opportunity_id: string; recommendation: string; status: string; decision_at: string }> {
  const res = await fetch(`${API_URL}/api/v1/opportunity/${id}/decide`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recommendation: body.recommendation ?? "yes", confidence: body.confidence ?? 0.8 }),
  });
  if (!res.ok) throw new Error(`Decision failed (${res.status})`);
  return res.json();
}

export async function getMemos(): Promise<MemoListItem[]> {
  if (!USE_FIXTURES) {
    const live = await tryFetch<{ memos: MemoListItem[] }>("/api/v1/memos");
    if (live) return live.memos;
  }
  return memoFixtures.map(toListItem);
}

export async function getMemoDetail(id: string): Promise<MemoDetail | null> {
  if (!USE_FIXTURES) {
    const live = await tryFetch<MemoDetail>(`/api/v1/memos/${id}`);
    if (live) {
      return {
        ...live,
        sections: (live.sections ?? []).map((s) => ({
          ...s,
          evidence: s.evidence ?? [],
        })),
      };
    }
    // Fallback: accept opportunity_id in the URL (older links / list glitches)
    const fromOpp = await memoDetailFromOpportunity(id);
    if (fromOpp) return fromOpp;
  }
  return memoFixtures.find((m) => m.id === id) ?? null;
}

/** Build a MemoDetail from opportunity payload when /memos/{id} is unavailable. */
async function memoDetailFromOpportunity(opportunityOrMemoId: string): Promise<MemoDetail | null> {
  const list = await tryFetch<{ memos: MemoListItem[] }>("/api/v1/memos");
  const match = list?.memos?.find(
    (m) => m.id === opportunityOrMemoId || m.opportunity_id === opportunityOrMemoId,
  );
  if (!match) return null;
  const opp = await tryFetch<OpportunityDetail>(`/api/v1/opportunity/${match.opportunity_id}`);
  if (!opp?.memo?.sections?.length) return null;
  return {
    id: match.id,
    opportunity_id: match.opportunity_id,
    company_name: opp.company_name,
    founder_name: opp.founder_name,
    source: opp.source,
    status: opp.status,
    recommendation: opp.recommendation,
    has_contradiction: opp.has_contradiction,
    snapshot: match.snapshot,
    created_at: match.created_at,
    updated_at: match.updated_at,
    sections: opp.memo.sections.map((s) => ({
      title: s.title,
      content: s.content ?? null,
      not_disclosed: s.not_disclosed,
      required: s.required,
      evidence: [],
    })),
  };
}

export interface PortfolioCompany {
  opportunity_id: string;
  company_name: string;
  company_sector?: string | null;
  company_domain?: string | null;
  founder_name: string;
  founder_id: string;
  source?: string | null;
  discovery_channel?: string | null;
  thesis_fit_score?: number | null;
  check_size_usd: number;
  recommendation: string;
  funded_at?: string | null;
  status: string;
}

function portfolioFromDashboard(dash: PipelineDashboard): PortfolioCompany[] {
  return dash.opportunities
    .filter((o) => o.status === "funded")
    .map((o) => ({
      opportunity_id: o.id,
      company_name: o.company_name,
      company_sector: (o as { company_sector?: string }).company_sector ?? null,
      company_domain: (o as { company_domain?: string }).company_domain ?? null,
      founder_name: o.founder_name,
      founder_id: o.founder_id,
      source: o.source,
      discovery_channel: o.discovery_channel,
      thesis_fit_score: o.thesis_fit_score,
      check_size_usd: (o as { check_size_usd?: number }).check_size_usd ?? 100_000,
      recommendation: (o as { recommendation?: string }).recommendation ?? "yes",
      funded_at: o.sla?.decision_at ?? null,
      status: "funded",
    }));
}

export async function getPortfolio(): Promise<PortfolioCompany[]> {
  if (!USE_FIXTURES) {
    const live = await tryFetch<{ companies: PortfolioCompany[] }>("/api/v1/portfolio");
    // Prefer live API even when empty — otherwise a just-funded company can be
    // masked by fixture/dashboard fallback after Approve investment.
    if (live && Array.isArray(live.companies)) return live.companies;
  }
  return portfolioFromDashboard(await getPipelineDashboard());
}

// ---------------------------------------------------------------------------
// Outbound sourcing + watchlist (docs/03-SOURCING.md §2-4)
// ---------------------------------------------------------------------------

export type WatchlistStage =
  | "discovered"
  | "scored"
  | "activation-candidate"
  | "outreach-sent"
  | "applied"
  | "screening";

export interface WatchlistSignal {
  channel: "github" | "hackernews" | "perplexity" | "web_search" | "arxiv" | "linkedin";
  [key: string]: unknown;
}

export interface WatchlistEntry {
  id: string;
  founder_id: string;
  founder_name: string;
  company_id: string | null;
  company_name: string | null;
  stage: WatchlistStage;
  conviction_score: number | null;
  promoted_via: string | null;
  signals: WatchlistSignal[];
  triggering_signal: string | null;
  opportunity_id: string | null;
  created_at: string;
  updated_at: string;
  confidence?: number;
  rationale?: string;
  promoted?: boolean;
  reason?: string;
  draft?: string;
}

export async function getWatchlist(): Promise<WatchlistEntry[]> {
  const res = await fetch(`${API_URL}/api/v1/sourcing/watchlist`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load watchlist (${res.status})`);
  const data = await res.json();
  return data.entries as WatchlistEntry[];
}

export async function discoverFounder(payload: {
  founder_name: string;
  company_name?: string;
  github_username?: string;
  hn_query?: string;
  linkedin_url?: string;
}): Promise<WatchlistEntry> {
  const res = await fetch(`${API_URL}/api/v1/sourcing/discover`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Discover failed (${res.status})`);
  return res.json();
}

async function postWatchlistAction(
  entryId: string,
  action: string
): Promise<WatchlistEntry & { dedupe?: DedupeInfo; screen_reason?: string; opportunity_id?: string }> {
  const res = await fetch(`${API_URL}/api/v1/sourcing/watchlist/${entryId}/${action}`, { method: "POST" });
  if (!res.ok) throw new Error(`${action} failed (${res.status})`);
  return res.json();
}

export const promoteWatchlistEntry = (id: string) => postWatchlistAction(id, "promote");
export const generateOutreach = (id: string) => postWatchlistAction(id, "outreach");
export const activateWatchlistEntry = (id: string) => postWatchlistAction(id, "activate");

// ---------------------------------------------------------------------------
// Perplexity research: thesis sourcing sweep + natural-language query
// (docs/05-CURSOR-SKILLS.md §2-3)
// ---------------------------------------------------------------------------

export interface EvidenceRef {
  source_type: string;
  source_locator: string;
  evidence_snippet: string;
  confidence: number;
  title?: string;
}

export interface SourcingSweepLead {
  query: string;
  answer: string;
  evidence: EvidenceRef[];
  bronze_id: string;
}

export interface SourcingSweepResult {
  thesis: string | null;
  thesis_id?: string;
  leads: SourcingSweepLead[];
  watchlist_entries?: WatchlistEntry[];
  error: string | null;
}

export async function runSourcingSweep(thesisId?: string): Promise<SourcingSweepResult> {
  const res = await fetch(`${API_URL}/api/v1/skills/thesis-sourcing-sweep/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thesis_id: thesisId ?? null }),
  });
  if (!res.ok) throw new Error(`Sourcing sweep failed (${res.status})`);
  return res.json();
}

export interface ClauseMatch {
  constraint: string;
  matched: boolean;
  explanation: string;
}

export interface NlQueryResultRow {
  opportunity_id: string;
  company_name: string;
  company_sector?: string | null;
  founder_name: string;
  match_count: number;
  match_ratio: number;
  clause_matches: ClauseMatch[];
  match_mode: string;
}

export interface NlQueryResponse {
  query: string;
  constraints: string[];
  decompose_mode: string;
  results: NlQueryResultRow[];
}

export async function runNaturalLanguageQuery(query: string): Promise<NlQueryResponse> {
  const res = await fetch(`${API_URL}/api/v1/query/natural-language`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Natural-language query failed (${res.status})`);
  return res.json();
}

export interface MemoryCitation {
  source_type: string | null;
  source_locator: string | null;
  snippet: string;
}

export interface AgentMessageResponse {
  mode: "search" | "action" | "chat" | "stats" | "memory";
  reply: string;
  skills_used: string[];
  citations: MemoryCitation[];
  search: NlQueryResponse | null;
}

/** Unified Ask entry — search filters run NL query; diligence verbs route to skills. */
export async function sendAgentMessage(message: string): Promise<AgentMessageResponse> {
  const res = await fetch(`${API_URL}/api/v1/agent/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error(`Agent message failed (${res.status})`);
  return res.json();
}
