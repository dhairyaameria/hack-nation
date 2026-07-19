"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Loader2 } from "lucide-react";
import { decideOpportunity } from "@/lib/api/client";

type Props = {
  opportunityId: string;
  alreadyApproved?: boolean;
  className?: string;
};

export function InvestButton({ opportunityId, alreadyApproved = false, className = "" }: Props) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [approved, setApproved] = useState(alreadyApproved);
  const [error, setError] = useState<string | null>(null);

  if (approved) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 rounded-md border border-brand/40 bg-accent px-3 py-1.5 text-sm font-medium text-brand-ink ${className}`}
      >
        <Check className="h-3.5 w-3.5" />
        Approved
      </span>
    );
  }

  async function onApprove(e: { preventDefault: () => void; stopPropagation: () => void }) {
    e.preventDefault();
    e.stopPropagation();
    setPending(true);
    setError(null);
    try {
      await decideOpportunity(opportunityId, { recommendation: "yes" });
      setApproved(true);
      router.push("/portfolio");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Decision failed");
      setPending(false);
    }
  }

  return (
    <div className={`flex flex-col items-end gap-1 ${className}`}>
      <button
        type="button"
        onClick={onApprove}
        disabled={pending}
        className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
      >
        {pending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
        {pending ? "Approving…" : "Approve investment"}
      </button>
      {error && <p className="text-xs text-bad max-w-[10rem] text-right">{error}</p>}
    </div>
  );
}
