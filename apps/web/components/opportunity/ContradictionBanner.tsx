import { AlertTriangle } from "lucide-react";

export function ContradictionBanner() {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 flex items-start gap-3">
      <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5 shrink-0" />
      <div className="text-sm text-red-900">
        <span className="font-medium">Validator caught a contradiction.</span>{" "}
        One or more claims in this deck conflict with independently corroborated
        evidence. Review before reading the memo.
      </div>
    </div>
  );
}
