"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getInboundApplications,
  submitApplication,
  type InboundApplication,
  type SubmitApplicationResult,
} from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";
import { InboundApplicationCard } from "@/components/inbound/InboundApplicationCard";

const VERDICT_STYLE: Record<string, string> = {
  pass: "bg-good-bg text-good border-good/30",
  reject: "bg-bad-bg text-bad border-bad-line",
  "needs-more-info": "bg-warn-bg text-warn border-warn-line",
};

export default function ApplyPage() {
  const router = useRouter();
  const [companyName, setCompanyName] = useState("");
  const [founderName, setFounderName] = useState("");
  const [deck, setDeck] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<SubmitApplicationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [apps, setApps] = useState<InboundApplication[]>([]);
  const [loadingApps, setLoadingApps] = useState(true);

  const refreshApps = useCallback(async () => {
    setLoadingApps(true);
    try {
      const list = await getInboundApplications();
      setApps(list);
    } catch {
      setApps([]);
    } finally {
      setLoadingApps(false);
    }
  }, []);

  useEffect(() => {
    void refreshApps();
  }, [refreshApps]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("company_name", companyName);
      formData.append("founder_name", founderName || "Unnamed founder");
      if (deck) formData.append("deck", deck);
      const res = await submitApplication(formData);
      setResult(res);
      setCompanyName("");
      setFounderName("");
      setDeck(null);
      await refreshApps();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed — is the API running?");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-10">
      <header className="space-y-1 max-w-xl">
        <h1 className="text-2xl font-semibold tracking-tight">Inbound Sources</h1>
        <p className="text-sm text-muted-foreground">
          Applications with pitch decks — preview the PDF, open the company profile.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="max-w-xl space-y-4 rounded-xl border p-5">
        <p className="text-sm font-medium">Submit application</p>
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="company">Company name</label>
          <input
            id="company"
            required
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            className="w-full rounded-md border px-3 py-2 text-sm bg-background"
            placeholder="Acme Robotics"
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="founder">Founder name</label>
          <input
            id="founder"
            value={founderName}
            onChange={(e) => setFounderName(e.target.value)}
            className="w-full rounded-md border px-3 py-2 text-sm bg-background"
            placeholder="Sam Rivera"
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="deck">Pitch deck (PDF)</label>
          <input
            id="deck"
            type="file"
            accept="application/pdf"
            onChange={(e) => setDeck(e.target.files?.[0] ?? null)}
            className="w-full rounded-md border px-3 py-2 text-sm bg-background"
          />
        </div>
        <button
          type="submit"
          disabled={submitting || !companyName}
          className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {submitting ? "Submitting…" : "Submit application"}
        </button>
      </form>

      {error && <p className="text-sm text-bad">{error}</p>}

      {result && (
        <div className="max-w-xl rounded-lg border p-4 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Fast screen verdict:</span>
            <Badge className={VERDICT_STYLE[result.screen_verdict]} variant="outline">
              {result.screen_verdict}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">{result.screen_reason}</p>
          <p className="text-sm text-muted-foreground">
            {result.claims_extracted} claim(s) extracted from {result.deck_filename ?? "no deck"}.
          </p>
          <div className="flex gap-3 pt-2">
            {result.company_id ? (
              <Link
                href={`/companies/${result.company_id}`}
                className="text-sm font-medium text-primary hover:underline"
              >
                View company profile →
              </Link>
            ) : (
              <Link
                href={`/opportunities/${result.opportunity_id}`}
                className="text-sm font-medium text-primary hover:underline"
              >
                View opportunity →
              </Link>
            )}
            <button
              type="button"
              onClick={() => router.refresh()}
              className="text-sm font-medium text-muted-foreground hover:underline"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      <section className="space-y-4">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Applications</h2>
            <p className="text-sm text-muted-foreground">
              Click a card to open the company profile and full deck.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void refreshApps()}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Refresh
          </button>
        </div>

        {loadingApps ? (
          <p className="text-sm text-muted-foreground">Loading applications…</p>
        ) : apps.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No inbound applications yet. Submit a deck above, or seed famous early-stage decks:
            <code className="ml-1 text-xs">python db/seed/load_awesome_decks.py</code>
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {apps.map((app) => (
              <InboundApplicationCard key={app.id} app={app} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
