"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { enrichFounder } from "@/lib/api/client";

export function RefreshFounderButton({ founderId }: { founderId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onClick() {
    setBusy(true);
    setError(null);
    try {
      await enrichFounder(founderId, true);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Refresh failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-1">
      <button
        type="button"
        onClick={onClick}
        disabled={busy}
        className="rounded-md border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted disabled:opacity-50"
      >
        {busy ? "Researching…" : "Refresh research"}
      </button>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
