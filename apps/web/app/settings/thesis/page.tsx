"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ThesisProfile } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ThesisSettingsPage() {
  const [theses, setTheses] = useState<ThesisProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/thesis`);
      const data = await res.json();
      setTheses(data);
    } catch {
      setTheses([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function activate(id: string) {
    setActivating(id);
    try {
      await fetch(`${API_URL}/api/v1/thesis/${id}/activate`, { method: "POST" });
      await load();
    } finally {
      setActivating(null);
    }
  }

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Fund Thesis</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Switching the active thesis re-ranks the pipeline by thesis fit.
        </p>
      </header>

      {loading && <p className="text-sm text-muted-foreground">Loading…</p>}

      <div className="space-y-4">
        {theses.map((t) => (
          <Card key={t.id} className={t.is_active ? "border-primary" : undefined}>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-2">
                <CardTitle className="text-base">{t.name}</CardTitle>
                {t.is_active && <Badge>Active</Badge>}
              </div>
              {!t.is_active && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => activate(t.id!)}
                  disabled={activating === t.id}
                >
                  {activating === t.id ? "Activating…" : "Activate"}
                </Button>
              )}
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex flex-wrap gap-1.5">
                {t.sectors.map((s) => (
                  <Badge key={s} variant="secondary">{s}</Badge>
                ))}
                {t.exclude_sectors.map((s) => (
                  <Badge key={s} variant="destructive">exclude: {s}</Badge>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-2 text-muted-foreground text-xs pt-1">
                <span>Stage: {t.stage}</span>
                <span>Geography: {t.geography}</span>
                <span>Check size: ${t.check_size_usd.toLocaleString()}</span>
                <span>Risk: {t.risk_appetite}</span>
                <span>Ownership target: {t.ownership_target_pct ?? "—"}%</span>
                <span>Watchlist threshold: {t.watchlist_promotion_threshold}</span>
              </div>
              {t.require_signals.length > 0 && (
                <div className="text-xs text-muted-foreground">
                  Requires: {t.require_signals.join(", ")}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
