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

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USE_FIXTURES = process.env.NEXT_PUBLIC_USE_FIXTURES === "true";

async function tryFetch<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function getPipelineDashboard() {
  if (!USE_FIXTURES) {
    const live = await tryFetch<typeof pipelineFixture>("/api/v1/opportunities");
    if (live) return live;
  }
  return pipelineFixture;
}

export async function getOpportunityDetail(id: string) {
  if (!USE_FIXTURES) {
    const live = await tryFetch<typeof opportunityFixture>(`/api/v1/opportunity/${id}`);
    if (live) return live;
  }
  // Fixture only has full detail for opp-contradiction; fall back to the
  // dashboard summary for everything else so every card is clickable.
  if (id === opportunityFixture.id) return opportunityFixture;
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
