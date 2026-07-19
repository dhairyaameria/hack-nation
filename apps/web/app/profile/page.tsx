"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import type { ThesisProfile } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function humanize(value: string): string {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .trim();
}

function formatCheck(usd: number): string {
  if (usd >= 1_000_000) return `$${(usd / 1_000_000).toFixed(usd % 1_000_000 === 0 ? 0 : 1)}M`;
  if (usd >= 1_000) return `$${(usd / 1_000).toFixed(usd % 1_000 === 0 ? 0 : 1)}K`;
  return `$${usd.toLocaleString()}`;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="font-mono text-[10px] uppercase tracking-[0.12em] text-faint">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-ink tabular-nums">{value}</dd>
    </div>
  );
}

function ThesisBody({ thesis }: { thesis: ThesisProfile }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-1.5">
        {thesis.sectors.map((s) => (
          <Badge key={s} variant="secondary" className="font-normal">
            {humanize(s)}
          </Badge>
        ))}
        {thesis.exclude_sectors.map((s) => (
          <Badge
            key={`ex-${s}`}
            variant="outline"
            className="border-line3 font-normal text-sub"
          >
            Exclude {humanize(s)}
          </Badge>
        ))}
      </div>

      <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3 lg:grid-cols-4">
        <Metric label="Stage" value={humanize(thesis.stage)} />
        <Metric label="Geography" value={thesis.geography} />
        <Metric label="Check size" value={formatCheck(thesis.check_size_usd)} />
        <Metric
          label="Ownership"
          value={
            thesis.ownership_target_pct != null
              ? `${thesis.ownership_target_pct}%`
              : "—"
          }
        />
        <Metric label="Risk" value={humanize(thesis.risk_appetite)} />
        <Metric
          label="Watchlist bar"
          value={`${Math.round(thesis.watchlist_promotion_threshold * 100)}%`}
        />
        {thesis.require_signals.length > 0 && (
          <Metric
            label="Requires"
            value={thesis.require_signals.map(humanize).join(", ")}
          />
        )}
        <Metric label="Version" value={`v${thesis.version}`} />
      </dl>

      {thesis.notes ? (
        <p className="border-t border-line pt-3 text-sm leading-relaxed text-sub">
          {thesis.notes}
        </p>
      ) : null}
    </div>
  );
}

export default function FundProfilePage() {
  const [theses, setTheses] = useState<ThesisProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/thesis`, { cache: "no-store" });
      if (!res.ok) throw new Error(`Failed to load theses (${res.status})`);
      const data = await res.json();
      setTheses(Array.isArray(data) ? data : []);
    } catch (err) {
      setTheses([]);
      setError(err instanceof Error ? err.message : "Failed to load fund profiles");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function activate(id: string) {
    setActivating(id);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/thesis/${id}/activate`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(`Activate failed (${res.status})`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Activate failed");
    } finally {
      setActivating(null);
    }
  }

  const active = useMemo(() => theses.find((t) => t.is_active) ?? null, [theses]);
  const others = useMemo(() => theses.filter((t) => !t.is_active), [theses]);

  return (
    <div className="mx-auto max-w-[880px] px-8 pb-20 pt-12">
      <header className="border-b border-ink pb-6">
        <p className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-sub">
          Settings
        </p>
        <h1 className="mt-2 font-serif text-[40px] font-medium leading-[1.05] tracking-[-0.01em] text-ink">
          Fund profile
        </h1>
        <p className="mt-3 max-w-xl text-sm leading-relaxed text-sub">
          The active thesis drives inbound screening, outbound conviction, and
          pipeline fit. Switch theses to re-rank the book.
        </p>
      </header>

      {loading && (
        <p className="mt-8 text-sm text-muted-foreground">Loading theses…</p>
      )}

      {error && (
        <p className="mt-6 rounded-[2px] border border-line bg-raise px-4 py-3 text-sm text-ink">
          {error}
        </p>
      )}

      {!loading && !error && theses.length === 0 && (
        <p className="mt-8 text-sm text-sub">No thesis profiles configured yet.</p>
      )}

      {active && (
        <section className="mt-8">
          <div className="mb-3 flex items-baseline justify-between gap-3">
            <h2 className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-sub">
              Active thesis
            </h2>
            <span className="rounded-[2px] bg-primary px-2 py-0.5 text-[11px] font-medium text-primary-foreground">
              Screening now
            </span>
          </div>
          <div className="rounded-[2px] border border-brand/40 bg-surface px-5 py-5 shadow-[inset_3px_0_0_0_var(--brand)]">
            <h3 className="text-lg font-semibold tracking-tight text-ink">
              {active.name}
            </h3>
            <div className="mt-4">
              <ThesisBody thesis={active} />
            </div>
          </div>
        </section>
      )}

      {others.length > 0 && (
        <section className="mt-10">
          <div className="mb-3 flex items-baseline justify-between gap-3">
            <h2 className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-sub">
              Available theses
            </h2>
            <span className="text-xs text-faint">
              {others.length} alternate{others.length === 1 ? "" : "s"}
            </span>
          </div>
          <ul className="divide-y divide-line rounded-[2px] border border-line bg-surface">
            {others.map((t) => (
              <li
                key={t.id}
                className="flex flex-col gap-4 px-5 py-5 sm:flex-row sm:items-start sm:justify-between"
              >
                <div className="min-w-0 flex-1 space-y-3">
                  <h3 className="text-base font-semibold tracking-tight text-ink">
                    {t.name}
                  </h3>
                  <ThesisBody thesis={t} />
                </div>
                <button
                  type="button"
                  onClick={() => t.id && activate(t.id)}
                  disabled={!t.id || activating === t.id}
                  className="shrink-0 self-start rounded-[2px] bg-primary px-3.5 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
                >
                  {activating === t.id ? "Activating…" : "Make active"}
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
