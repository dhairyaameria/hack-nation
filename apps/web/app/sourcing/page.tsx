"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  activateWatchlistEntry,
  discoverFounder,
  generateOutreach,
  getWatchlist,
  promoteWatchlistEntry,
  type WatchlistEntry,
} from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";

const STAGE_STYLE: Record<string, string> = {
  discovered: "bg-slate-100 text-slate-700 border-slate-300",
  scored: "bg-blue-100 text-blue-800 border-blue-300",
  "activation-candidate": "bg-violet-100 text-violet-800 border-violet-300",
  "outreach-sent": "bg-amber-100 text-amber-800 border-amber-300",
  applied: "bg-cyan-100 text-cyan-800 border-cyan-300",
  screening: "bg-emerald-100 text-emerald-800 border-emerald-300",
};

export default function SourcingPage() {
  const [entries, setEntries] = useState<WatchlistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [founderName, setFounderName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [githubUsername, setGithubUsername] = useState("");
  const [hnQuery, setHnQuery] = useState("");
  const [discovering, setDiscovering] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [outreachDraft, setOutreachDraft] = useState<{ id: string; draft: string } | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      setEntries(await getWatchlist());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load watchlist — is the API running?");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleDiscover(e: React.FormEvent) {
    e.preventDefault();
    setDiscovering(true);
    setError(null);
    try {
      await discoverFounder({
        founder_name: founderName,
        company_name: companyName || undefined,
        github_username: githubUsername || undefined,
        hn_query: hnQuery || undefined,
      });
      setFounderName("");
      setCompanyName("");
      setGithubUsername("");
      setHnQuery("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Discover failed");
    } finally {
      setDiscovering(false);
    }
  }

  async function handleAction(id: string, action: "promote" | "outreach" | "activate") {
    setBusyId(id);
    setError(null);
    try {
      const fn = action === "promote" ? promoteWatchlistEntry : action === "outreach" ? generateOutreach : activateWatchlistEntry;
      const result = await fn(id);
      if (action === "promote" && result.promoted === false) {
        setError(`Not promoted: ${result.reason}`);
      }
      if (action === "outreach" && result.draft) {
        setOutreachDraft({ id, draft: result.draft });
      }
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : `${action} failed`);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Sourcing &amp; Watchlist</h1>
        <p className="text-sm text-muted-foreground">
          Outbound discovery via live GitHub + Hacker News signals. Promotion requires multi-signal
          corroboration above the active thesis&apos;s conviction threshold — no signal is never scored
          as a negative, only as &quot;unknown&quot;.
        </p>
      </header>

      <form onSubmit={handleDiscover} className="rounded-lg border p-4 space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Discover a candidate</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Founder name</label>
            <input
              required
              value={founderName}
              onChange={(e) => setFounderName(e.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm"
              placeholder="Ada Lovelace"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Company name (optional)</label>
            <input
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm"
              placeholder="Analytical Engines Inc."
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">GitHub username (optional)</label>
            <input
              value={githubUsername}
              onChange={(e) => setGithubUsername(e.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm"
              placeholder="octocat"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">HN search query (optional)</label>
            <input
              value={hnQuery}
              onChange={(e) => setHnQuery(e.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm"
              placeholder="defaults to company/founder name"
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={discovering || !founderName}
          className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {discovering ? "Running connectors…" : "Discover"}
        </button>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Watchlist ({entries.length})
        </h2>
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : entries.length === 0 ? (
          <p className="text-sm text-muted-foreground">No candidates discovered yet.</p>
        ) : (
          <div className="space-y-3">
            {entries.map((entry) => (
              <div key={entry.id} className="rounded-lg border p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">
                      {entry.founder_name}
                      {entry.company_name && <span className="text-muted-foreground"> — {entry.company_name}</span>}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {entry.signals.map((s) => s.channel).join(" + ") || "no signals yet"} · conviction{" "}
                      {entry.conviction_score ?? "unknown (cold start)"}
                      {entry.promoted_via && ` · promoted via ${entry.promoted_via}`}
                    </p>
                  </div>
                  <Badge className={STAGE_STYLE[entry.stage]} variant="outline">
                    {entry.stage}
                  </Badge>
                </div>

                {outreachDraft?.id === entry.id && (
                  <pre className="whitespace-pre-wrap rounded-md bg-muted/40 p-3 text-xs">{outreachDraft.draft}</pre>
                )}

                <div className="flex gap-3 pt-1">
                  {entry.stage === "scored" && (
                    <button
                      onClick={() => handleAction(entry.id, "promote")}
                      disabled={busyId === entry.id}
                      className="text-sm font-medium text-primary hover:underline disabled:opacity-50"
                    >
                      Promote
                    </button>
                  )}
                  {entry.stage === "activation-candidate" && (
                    <button
                      onClick={() => handleAction(entry.id, "outreach")}
                      disabled={busyId === entry.id}
                      className="text-sm font-medium text-primary hover:underline disabled:opacity-50"
                    >
                      Generate outreach
                    </button>
                  )}
                  {(entry.stage === "activation-candidate" || entry.stage === "outreach-sent") && (
                    <button
                      onClick={() => handleAction(entry.id, "activate")}
                      disabled={busyId === entry.id}
                      className="text-sm font-medium text-primary hover:underline disabled:opacity-50"
                    >
                      Activate → create opportunity
                    </button>
                  )}
                  {entry.opportunity_id && (
                    <Link href={`/opportunities/${entry.opportunity_id}`} className="text-sm font-medium text-emerald-700 hover:underline">
                      View opportunity →
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
