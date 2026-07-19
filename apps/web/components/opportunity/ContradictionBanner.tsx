import { AlertTriangle } from "lucide-react";

export function ContradictionBanner() {
  return (
    <div className="rounded-[2px] border border-brand/30 bg-accent px-4 py-3 flex items-start gap-3">
      <AlertTriangle className="h-4 w-4 text-brand mt-0.5 shrink-0" />
      <div className="text-sm text-ink">
        <span className="font-medium text-brand-ink">Validator caught a contradiction.</span>{" "}
        One or more claims in this deck conflict with independently corroborated
        evidence. Review the scores and claims before deciding.
      </div>
    </div>
  );
}
