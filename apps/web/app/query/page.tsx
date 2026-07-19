"use client";

import { useState } from "react";
import Link from "next/link";
import { runNaturalLanguageQuery, type NlQueryResponse } from "@/lib/api/client";

const EXAMPLE_QUERIES = [
  "technical founder, AI infra, enterprise traction, no prior VC backing",
  "cold-start founder with strong execution signal, low network embeddedness",
  "sector matches thesis, contradiction flagged in claims",
];

export default function NaturalLanguageQueryPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<NlQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await runNaturalLanguageQuery(query));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Natural-Language Query</h1>
        <p className="text-sm text-muted-foreground">
          One-pass resolution of a compound query into structured constraints, with a per-clause
          match explanation for every opportunity — never a single opaque relevance score.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-3">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={3}
          placeholder="e.g. technical founder, Berlin, AI infra, enterprise traction, no prior VC backing"
          className="w-full rounded-md border px-3 py-2 text-sm"
        />
        <div className="flex items-center justify-between">
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_QUERIES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => setQuery(ex)}
                className="text-xs rounded-full border px-3 py-1 text-muted-foreground hover:bg-muted/50"
              >
                {ex}
              </button>
            ))}
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="shrink-0 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Resolving…" : "Search"}
          </button>
        </div>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="space-y-4">
          <div className="rounded-lg border p-4 space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Decomposed constraints <span className="font-normal">({result.decompose_mode})</span>
            </p>
            <div className="flex flex-wrap gap-2">
              {result.constraints.map((c, i) => (
                <span key={i} className="rounded-full bg-muted px-3 py-1 text-xs">
                  {c}
                </span>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            {result.results.map((r) => (
              <div
                key={r.opportunity_id}
                className="rounded-lg border p-4 space-y-2 hover:border-primary/50 transition-colors"
              >
                <div className="flex items-center justify-between gap-3">
                  <Link
                    href={`/opportunities/${r.opportunity_id}`}
                    className="font-medium hover:underline"
                  >
                    {r.company_name}
                    <span className="text-muted-foreground font-normal"> — {r.founder_name}</span>
                    {r.company_sector && (
                      <span className="ml-2 text-xs text-muted-foreground font-normal">
                        ({r.company_sector})
                      </span>
                    )}
                  </Link>
                  <span className="text-sm font-semibold tabular-nums shrink-0">
                    {r.match_count}/{result.constraints.length} matched
                  </span>
                </div>
                <div className="space-y-1 border-t pt-2">
                  {r.clause_matches.map((m, i) => (
                    <p key={i} className="text-xs flex gap-2">
                      <span className={m.matched ? "text-emerald-600" : "text-muted-foreground"}>
                        {m.matched ? "✓" : "✕"}
                      </span>
                      <span>
                        <span className="font-medium">{m.constraint}</span>
                        {m.explanation && <span className="text-muted-foreground"> — {m.explanation}</span>}
                      </span>
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
