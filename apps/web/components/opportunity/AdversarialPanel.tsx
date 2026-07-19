import { Scale, TrendingDown, TrendingUp } from "lucide-react";
import type { AdversarialView } from "@/lib/types";
import { confidenceLevel } from "@/components/ui/ds";

const SEVERITY_STYLE: Record<string, string> = {
  high: "border-bad-line bg-bad-bg text-bad",
  medium: "border-warn-line bg-warn-bg text-warn",
  low: "border-line bg-raise text-sub",
};

const RECOMMENDATION_COPY: Record<string, string> = {
  yes: "System leans yes",
  no: "System leans no",
  "needs-more-info": "System: needs more info",
};

/**
 * Bull vs. bear side by side — the adversarial stage's case against the memo,
 * shown before the human closes the decision. The recommendation is the
 * system's call to overrule, never an auto-approval.
 */
export function AdversarialPanel({ view }: { view: AdversarialView }) {
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Adversarial View
        </h2>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-[2px] border border-line bg-raise px-2 py-1 font-mono text-[10.5px] uppercase tracking-[0.06em]">
            <Scale className="h-3 w-3" />
            {RECOMMENDATION_COPY[view.recommendation] ?? view.recommendation}
          </span>
          <span className="rounded-[2px] border border-line bg-raise px-2 py-1 font-mono text-[10.5px] uppercase tracking-[0.06em] text-sub">
            {confidenceLevel(view.confidence)} confidence
          </span>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-lg border border-line bg-raise p-4">
          <div className="mb-2 inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.1em] text-good">
            <TrendingUp className="h-3 w-3" /> Bull case
          </div>
          <p className="text-sm leading-relaxed">
            {view.bull_summary ?? "No independently verified positive signal yet."}
          </p>
        </div>
        <div className="rounded-lg border border-line bg-raise p-4">
          <div className="mb-2 inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.1em] text-bad">
            <TrendingDown className="h-3 w-3" /> Bear case
          </div>
          <p className="text-sm leading-relaxed">
            {view.bear_summary ?? "No bear case articulated — treat with suspicion, not comfort."}
          </p>
        </div>
      </div>

      {view.bear_points.length > 0 && (
        <ul className="space-y-2">
          {view.bear_points.map((p, i) => (
            <li key={i} className="flex items-start gap-2.5 text-sm">
              <span
                className={`mt-0.5 shrink-0 rounded-[2px] border px-1.5 py-0.5 font-mono text-[9.5px] uppercase tracking-[0.06em] ${
                  SEVERITY_STYLE[p.severity] ?? SEVERITY_STYLE.low
                }`}
              >
                {p.severity}
              </span>
              <span>
                {p.point}
                {p.basis && <span className="block text-xs text-muted-foreground">{p.basis}</span>}
              </span>
            </li>
          ))}
        </ul>
      )}

      {view.kill_criteria.length > 0 && (
        <div className="rounded-lg border border-line bg-muted/30 p-4">
          <div className="mb-2 font-mono text-[10.5px] uppercase tracking-[0.1em] text-sub">
            Kill criteria — walk away if any of these turn out true
          </div>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {view.kill_criteria.map((k, i) => (
              <li key={i}>{k}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
