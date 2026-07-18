"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { submitApplication, type SubmitApplicationResult } from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";

const VERDICT_STYLE: Record<string, string> = {
  pass: "bg-emerald-100 text-emerald-800 border-emerald-300",
  reject: "bg-red-100 text-red-800 border-red-300",
  "needs-more-info": "bg-amber-100 text-amber-800 border-amber-300",
};

export default function ApplyPage() {
  const router = useRouter();
  const [companyName, setCompanyName] = useState("");
  const [founderName, setFounderName] = useState("");
  const [deck, setDeck] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<SubmitApplicationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed — is the API running?");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="p-8 max-w-xl mx-auto space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Apply</h1>
        <p className="text-sm text-muted-foreground">
          Minimal-friction inbound intake — company name + optional deck. No 40-field form.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="company">Company name</label>
          <input
            id="company"
            required
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            className="w-full rounded-md border px-3 py-2 text-sm"
            placeholder="Acme Robotics"
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="founder">Founder name</label>
          <input
            id="founder"
            value={founderName}
            onChange={(e) => setFounderName(e.target.value)}
            className="w-full rounded-md border px-3 py-2 text-sm"
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
            className="w-full rounded-md border px-3 py-2 text-sm"
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

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="rounded-lg border p-4 space-y-2">
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
            <Link
              href={`/opportunities/${result.opportunity_id}`}
              className="text-sm font-medium text-primary hover:underline"
            >
              View opportunity →
            </Link>
            <button
              onClick={() => router.push("/")}
              className="text-sm font-medium text-muted-foreground hover:underline"
            >
              Back to pipeline
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
