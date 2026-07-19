"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getInboundApplications,
  type InboundApplication,
} from "@/lib/api/client";
import { InboundApplicationCard } from "@/components/inbound/InboundApplicationCard";

export default function ApplyPage() {
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

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <header className="flex items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Inbound Sources</h1>
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
      </header>

      {loadingApps ? (
        <p className="text-sm text-muted-foreground">Loading applications…</p>
      ) : apps.length === 0 ? (
        <p className="text-sm text-muted-foreground">No inbound applications yet.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {apps.map((app) => (
            <InboundApplicationCard key={app.id} app={app} />
          ))}
        </div>
      )}
    </div>
  );
}
