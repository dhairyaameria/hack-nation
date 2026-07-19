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
import { MarkdownBrief } from "@/components/company/MarkdownBrief";
import { clipText, plainSnippet } from "@/lib/utils";

const STAGE_STYLE: Record<string, string> = {
  discovered: "bg-line2 text-sub border-line3",
  scored: "bg-raise text-brand-ink border-line3",
  "activation-candidate": "bg-raise text-brand-ink border-brand/40",
  "outreach-sent": "bg-warn-bg text-warn border-warn-line",
  applied: "bg-raise text-ink border-line3",
  screening: "bg-good-bg text-good border-good/30",
};

/** Discover form + thesis sweep + watchlist — opened from Outbound Sources via Find Lead. */
export function FindLeadPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [entries, setEntries] = useState<WatchlistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [founderName, setFounderName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [githubUsername, setGithubUsername] = useState("");
  const [hnQuery, setHnQuery] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [discovering, setDiscovering] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
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
        linkedin_url: linkedinUrl || undefined,
      });
      setFounderName("");
      setCompanyName("");
      setGithubUsername("");
      setHnQuery("");
      setLinkedinUrl("");
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
    setNotice(null);
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
      if (action === "activate" && result.dedupe?.action === "attached") {
        const oppId = result.opportunity_id;
        setNotice(
          oppId
            ? `Already in pipeline (${result.dedupe.prior_status ?? "open"}) — linked to existing opportunity. Run Analyze to refresh.`
            : `Already in pipeline (${result.dedupe.prior_status ?? "open"}).`
        );
      }
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : `${action} failed`);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      {/* Backdrop — click to collapse; does not affect card layout */}
      <button
        type="button"
        aria-label="Close find lead"
        onClick={onClose}
        className={`fixed inset-0 z-40 bg-ink/25 transition-opacity duration-200 ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      />

      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Find Lead"
        className={`fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-border bg-background shadow-xl transition-transform duration-200 ease-out ${
          open ? "translate-x-0" : "translate-x-full pointer-events-none"
        }`}
      >
        <div className="flex items-start justify-between gap-3 border-b border-border px-5 py-4">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold tracking-tight">Find Lead</h2>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              GitHub, HN, arXiv, LinkedIn, Perplexity, Tavily — multi-signal before promote.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-md px-2 py-1 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            Close
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
      <form onSubmit={handleDiscover} className="rounded-lg border p-4 space-y-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Discover a candidate
        </h3>
        <div className="grid grid-cols-1 gap-3">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Founder name</label>
            <input
              required
              value={founderName}
              onChange={(e) => setFounderName(e.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm bg-background"
              placeholder="Ada Lovelace"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Company name (optional)</label>
            <input
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm bg-background"
              placeholder="Analytical Engines Inc."
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">GitHub username (optional)</label>
            <input
              value={githubUsername}
              onChange={(e) => setGithubUsername(e.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm bg-background"
              placeholder="octocat"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Hacker News query (optional)</label>
            <input
              value={hnQuery}
              onChange={(e) => setHnQuery(e.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm bg-background"
              placeholder="Show HN … (defaults to company/founder)"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">LinkedIn URL (optional)</label>
            <input
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm bg-background"
              placeholder="https://linkedin.com/in/…"
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={discovering || !founderName}
          className="w-full rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {discovering ? "Running connectors…" : "Discover"}
        </button>
      </form>

      {error && <p className="text-sm text-bad">{error}</p>}
      {notice && <p className="text-sm text-brand-ink">{notice}</p>}

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
            {sweep.error && <p className="text-sm text-warn">{sweep.error}</p>}
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
            {sweep.leads.map((lead, i) => {
              const citeUrls = lead.evidence
                .map((e) => e.source_locator)
                .filter((u): u is string => Boolean(u));
              return (
              <div key={i} className="rounded-md bg-muted/30 p-3 space-y-2">
                <p className="text-xs font-medium text-muted-foreground">{lead.query}</p>
                {lead.answer ? (
                  <MarkdownBrief
                    content={lead.answer}
                    citations={citeUrls}
                    compact
                  />
                ) : null}
                {lead.evidence.length > 0 && (
                  <ul className="space-y-1 border-t pt-2">
                    {lead.evidence.slice(0, 4).map((e, j) => (
                      <li key={`${e.source_locator}-${j}`}>
                        <ExternalLink
                          href={e.source_locator}
                          className="inline text-[11px] text-brand-ink hover:underline break-all"
                        >
                          [{j + 1}] {e.title || e.source_locator}
                        </ExternalLink>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              );
            })}
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

                {entry.signals.some(
                  (s) =>
                    s.channel === "perplexity" ||
                    s.channel === "web_search" ||
                    s.channel === "linkedin"
                ) && (
                  <div className="space-y-2 rounded-md bg-muted/30 p-3 text-xs">
                    {entry.signals
                      .filter((s) => s.channel === "linkedin")
                      .map((s, i) => {
                        const url = typeof s.profile_url === "string" ? s.profile_url : null;
                        return (
                          <div key={`li-${i}`} className="space-y-1">
                            <p className="font-medium text-muted-foreground">LinkedIn (public web)</p>
                            {url ? (
                              <ExternalLink
                                href={url}
                                className="inline text-brand-ink hover:underline break-all"
                              >
                                {url}
                              </ExternalLink>
                            ) : (
                              <p className="text-muted-foreground">No profile URL resolved</p>
                            )}
                            {Boolean(s.headline || s.snippet) && (
                              <p className="leading-relaxed">
                                {String(s.headline ?? "")}
                                {s.headline && s.snippet ? " — " : ""}
                                {plainSnippet(String(s.snippet ?? ""), 240)}
                              </p>
                            )}
                          </div>
                        );
                      })}
                    {entry.signals
                      .filter((s) => s.channel === "perplexity")
                      .map((s, i) => {
                        const citations = dedupeUrls(
                          Array.isArray(s.citations) ? (s.citations as string[]) : []
                        ).slice(0, 4);
                        const answer = String(s.answer ?? "");
                        return (
                          <div key={`pplx-${i}`} className="space-y-1">
                            <p className="font-medium text-muted-foreground">Perplexity</p>
                            {answer ? (
                              <MarkdownBrief
                                content={clipText(answer, 1200)}
                                citations={citations}
                                compact
                              />
                            ) : null}
                            {citations.length > 0 && (
                              <ul className="space-y-1">
                                {citations.map((url, j) => (
                                  <li key={url}>
                                    <ExternalLink
                                      href={url}
                                      className="inline text-brand-ink hover:underline break-all"
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
                                    className="inline text-brand-ink hover:underline break-all"
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
                      className="text-sm font-medium text-good hover:underline"
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
      </aside>
    </>
  );
}
