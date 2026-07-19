"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { enrichFounder } from "@/lib/api/client";

/** Fire-and-forget research after first paint — never blocks SSR. */
export function AutoEnrichFounder({ founderId }: { founderId: string }) {
  const router = useRouter();
  const started = useRef(false);
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    setStatus("loading");
    enrichFounder(founderId, false)
      .then(() => {
        setStatus("done");
        router.refresh();
      })
      .catch(() => setStatus("error"));
  }, [founderId, router]);

  if (status === "idle" || status === "done") return null;
  if (status === "error") {
    return <p className="text-xs text-muted-foreground">Auto-research failed — use Refresh research.</p>;
  }
  return <p className="text-xs text-muted-foreground">Pulling Perplexity / Tavily research…</p>;
}
