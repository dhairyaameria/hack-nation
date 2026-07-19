"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  discoverFounder,
  runFounderSourcingSweep,
  type SourcingSweepResult,
} from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";

/** Thesis founder sweep + single-founder discover — for Founder Book. */
export function FounderSourcePanel() {
  const router = useRouter();
  const [founderName, setFounderName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [discovering, setDiscovering] = useState(false);
  const [sweeping, setSweeping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sweep, setSweep] = useState<SourcingSweepResult | null>(null);

  async function handleDiscover(e: React.FormEvent) {
    e.preventDefault();
    if (!founderName.trim()) return;
    setDiscovering(true);
    setError(null);
    try {
      const entry = await discoverFounder({
        founder_name: founderName.trim(),
        company_name: companyName.trim() || undefined,
      });
      setFounderName("");
      setCompanyName("");
      if (entry.founder_id) {
        router.push(`/founders/${entry.founder_id}`);
        router.refresh();
      } else {
        router.refresh();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Discover failed");
    } finally {
      setDiscovering(false);
    }
  }

  async function handleSweep() {
    setSweeping(true);
    setError(null);
    setSweep(null);
    try {
      const result = await runFounderSourcingSweep();
      setSweep(result);
      if (result.error) setError(result.error);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Founder sweep failed");
    } finally {
      setSweeping(false);
    }
  }

  return (
    <section className="space-y-4 rounded-xl border border-border bg-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold tracking-tight">Source founders</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Perplexity + Tavily research against the active thesis — same stack as company
            outbound, founder-first.
          </p>
        </div>
        <button
          type="button"
          onClick={handleSweep}
          disabled={sweeping}
          className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground disabled:opacity-50"
        >
          {sweeping ? "Sweeping…" : "Run founder sweep"}
        </button>
      </div>

      <form onSubmit={handleDiscover} className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
        <input
          value={founderName}
          onChange={(e) => setFounderName(e.target.value)}
          placeholder="Founder name"
          className="rounded-md border border-border bg-background px-3 py-2 text-sm"
          required
        />
        <input
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          placeholder="Company (optional)"
          className="rounded-md border border-border bg-background px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={discovering}
          className="rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"
        >
          {discovering ? "Researching…" : "Research founder"}
        </button>
      </form>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {sweep && !sweep.error && (
        <div className="space-y-2 border-t border-border pt-3">
          <p className="text-xs text-muted-foreground">
            Landed {sweep.watchlist_entries?.length ?? 0} watchlist lead
            {(sweep.watchlist_entries?.length ?? 0) === 1 ? "" : "s"} from{" "}
            <span className="font-medium text-foreground">{sweep.thesis}</span>
          </p>
          <div className="flex flex-wrap gap-2">
            {(sweep.watchlist_entries || []).slice(0, 8).map((e) => (
              <Badge key={e.id} variant="secondary">
                {e.founder_name || "Founder"}
                {e.company_name ? ` · ${e.company_name}` : ""}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
