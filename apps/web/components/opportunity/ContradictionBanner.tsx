import { AlertTriangle } from "lucide-react";

export function ContradictionBanner() {
  return (
    <div className="rounded-[2px] border border-bad-line bg-bad-bg px-4 py-3 flex items-start gap-3">
      <AlertTriangle className="h-4 w-4 text-bad mt-0.5 shrink-0" />
      <div className="text-sm text-bad">
        <span className="font-medium">Validator caught a contradiction.</span>{" "}
        One or more claims in this deck conflict with independently corroborated
        evidence. Review before reading the memo.
      </div>
    </div>
  );
}
