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
  return (networkGraphFixture as Record<string, unknown>)[founderId] ?? null;
}

export interface SubmitApplicationResult {
  opportunity_id: string;
  company_name: string;
  deck_filename: string | null;
  claims_extracted: number;
  screen_verdict: "pass" | "reject" | "needs-more-info";
  screen_reason: string;
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
