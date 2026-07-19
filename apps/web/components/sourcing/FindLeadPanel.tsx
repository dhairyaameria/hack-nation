"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  activateWatchlistEntry,
  discoverFounder,
  generateOutreach,
  getWatchlist,
  promoteWatchlistEntry,
  runSourcingSweep,
  type SourcingSweepResult,
  type WatchlistEntry,
} from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, dedupeUrls } from "@/components/ui/ExternalLink";

const STAGE_STYLE: Record<string, string> = {
  discovered: "bg-slate-100 text-slate-700 border-slate-300",
  scored: "bg-blue-100 text-blue-800 border-blue-300",
  "activation-candidate": "bg-violet-100 text-violet-800 border-violet-300",
  "outreach-sent": "bg-amber-100 text-amber-800 border-amber-300",
  applied: "bg-cyan-100 text-cyan-800 border-cyan-300",
  screening: "bg-emerald-100 text-emerald-800 border-emerald-300",
};

/** Discover form + thesis sweep + watchlist — opened from Outbound Sources via Find Lead. */
export function FindLeadPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
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
  const [sweep, setSweep] = useState<SourcingSweepResult | null>(null);
  const [sweeping, setSweeping] = useState(false);

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
    if (open) refresh();
  }, [open]);

  if (!open) return null;

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

  async function handleSweep() {
    setSweeping(true);
    setError(null);
    try {
      const result = await runSourcingSweep();
      setSweep(result);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sourcing sweep failed");
    } finally {
      setSweeping(false);
    }
  }

  async function handleAction(id: string, action: "promote" | "outreach" | "activate") {
    setBusyId(id);
    setError(null);
    try {
      const fn =
        action === "promote" ? promoteWatchlistEntry : action === "outreach" ? generateOutreach : activateWatchlistEntry;
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
    <div className="rounded-lg border bg-background p-5 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Find Lead</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Outbound discovery via GitHub, HN, arXiv, Perplexity, and Tavily. Promotion needs
            multi-signal corroboration — no signal is never scored as a negative.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="shrink-0 text-sm text-muted-foreground hover:text-foreground"
        >
          Close
        </button>
      </div>

      <form onSubmit={handleDiscover} className="rounded-lg border p-4 space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Discover a candidate
        </h3>
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

      <section className="rounded-lg border p-4 space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Thesis sourcing sweep
            </h3>
            <p className="text-xs text-muted-foreground mt-1">
              Live Perplexity research from the active thesis. Leads land on the watchlist as
              candidates, never pre-trusted facts.
            </p>
          </div>
          <button
            type="button"
            onClick={handleSweep}
            disabled={sweeping}
            className="shrink-0 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {sweeping ? "Researching…" : "Run sweep"}
          </button>
        </div>

        {sweep && (
          <div className="space-y-3 border-t pt-3">
            {sweep.error && <p className="text-sm text-amber-700">{sweep.error}</p>}
            {sweep.thesis && (
              <p className="text-xs text-muted-foreground">
                Thesis: <span className="font-medium">{sweep.thesis}</span> · {sweep.leads.length}{" "}
                querie(s) with results
                {sweep.watchlist_entries && sweep.watchlist_entries.length > 0 && (
                  <>
                    {" "}
                    · landed <span className="font-medium">{sweep.watchlist_entries.length}</span>{" "}
                    watchlist candidate(s)
                  </>
                )}
              </p>
            )}
            {sweep.leads.map((lead, i) => (
              <div key={i} className="rounded-md bg-muted/30 p-3 space-y-2">
                <p className="text-xs font-medium text-muted-foreground">{lead.query}</p>
                <p className="text-sm whitespace-pre-wrap">{lead.answer}</p>
                {lead.evidence.length > 0 && (
                  <ul className="space-y-1 border-t pt-2">
                    {lead.evidence.slice(0, 4).map((e, j) => (
                      <li key={`${e.source_locator}-${j}`}>
                        <ExternalLink
                          href={e.source_locator}
                          className="inline text-[11px] text-blue-700 hover:underline break-all"
                        >
                          [{j + 1}] {e.title || e.source_locator}
                        </ExternalLink>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Watchlist ({entries.length})
        </h3>
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
                      {entry.company_name && (
                        <span className="text-muted-foreground"> — {entry.company_name}</span>
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {entry.signals.map((s) => s.channel).join(" + ") || "no signals yet"} ·
                      conviction {entry.conviction_score ?? "unknown (cold start)"}
                      {entry.promoted_via && ` · promoted via ${entry.promoted_via}`}
                    </p>
                  </div>
                  <Badge className={STAGE_STYLE[entry.stage]} variant="outline">
                    {entry.stage}
                  </Badge>
                </div>

                {entry.signals.some((s) => s.channel === "perplexity" || s.channel === "web_search") && (
                  <div className="space-y-2 rounded-md bg-muted/30 p-3 text-xs">
                    {entry.signals
                      .filter((s) => s.channel === "perplexity")
                      .map((s, i) => {
                        const citations = dedupeUrls(
                          Array.isArray(s.citations) ? (s.citations as string[]) : []
                        ).slice(0, 4);
                        return (
                          <div key={`pplx-${i}`} className="space-y-1">
                            <p className="font-medium text-muted-foreground">Perplexity</p>
                            <p className="whitespace-pre-wrap leading-relaxed">
                              {String(s.answer ?? "").slice(0, 600)}
                            </p>
                            {citations.length > 0 && (
                              <ul className="space-y-1">
                                {citations.map((url, j) => (
                                  <li key={url}>
                                    <ExternalLink
                                      href={url}
                                      className="inline text-blue-700 hover:underline break-all"
                                    >
                                      [{j + 1}] {url}
                                    </ExternalLink>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        );
                      })}
                    {entry.signals
                      .filter((s) => s.channel === "web_search")
                      .map((s, i) => {
                        const results = Array.isArray(s.results)
                          ? (s.results as { title?: string; url?: string }[])
                          : [];
                        const seen = new Set<string>();
                        const unique = results
                          .filter((r) => {
                            if (!r.url || seen.has(r.url)) return false;
                            seen.add(r.url);
                            return true;
                          })
                          .slice(0, 4);
                        return (
                          <div key={`tav-${i}`} className="space-y-1 border-t pt-2">
                            <p className="font-medium text-muted-foreground">Tavily web search</p>
                            <ul className="space-y-1">
                              {unique.map((r, j) => (
                                <li key={r.url}>
                                  <ExternalLink
                                    href={r.url!}
                                    className="inline text-blue-700 hover:underline break-all"
                                  >
                                    [{j + 1}] {r.title || r.url}
                                  </ExternalLink>
                                </li>
                              ))}
                            </ul>
                          </div>
                        );
                      })}
                  </div>
                )}

                {outreachDraft?.id === entry.id && (
                  <pre className="whitespace-pre-wrap rounded-md bg-muted/40 p-3 text-xs">
                    {outreachDraft.draft}
                  </pre>
                )}

                <div className="flex gap-3 pt-1">
                  {entry.stage === "scored" && (
                    <button
                      type="button"
                      onClick={() => handleAction(entry.id, "promote")}
                      disabled={busyId === entry.id}
                      className="text-sm font-medium text-primary hover:underline disabled:opacity-50"
                    >
                      Promote
                    </button>
                  )}
                  {entry.stage === "activation-candidate" && (
                    <button
                      type="button"
                      onClick={() => handleAction(entry.id, "outreach")}
                      disabled={busyId === entry.id}
                      className="text-sm font-medium text-primary hover:underline disabled:opacity-50"
                    >
                      Generate outreach
                    </button>
                  )}
                  {(entry.stage === "activation-candidate" || entry.stage === "outreach-sent") && (
                    <button
                      type="button"
                      onClick={() => handleAction(entry.id, "activate")}
                      disabled={busyId === entry.id}
                      className="text-sm font-medium text-primary hover:underline disabled:opacity-50"
                    >
                      Activate → create opportunity
                    </button>
                  )}
                  {entry.opportunity_id && (
                    <Link
                      href={`/opportunities/${entry.opportunity_id}`}
                      className="text-sm font-medium text-emerald-700 hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
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
