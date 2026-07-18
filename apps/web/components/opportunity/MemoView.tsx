import { Badge } from "@/components/ui/badge";
import type { Memo } from "@/lib/types";

/** Missing sections are always a visible badge — never hidden (docs/00-OVERVIEW.md §4 rule 3). */
export function MemoView({ memo }: { memo: Memo | null | undefined }) {
  if (!memo) {
    return <p className="text-sm text-muted-foreground italic">Memo not generated yet.</p>;
  }

  return (
    <div className="space-y-4">
      {memo.sections.map((section, i) => (
        <div key={i} className="space-y-1">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold">{section.title}</h4>
            {section.not_disclosed && (
              <Badge variant="outline" className="text-amber-700 border-amber-300 bg-amber-50">
                Not disclosed
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            {section.content ?? "Unavailable at this stage."}
          </p>
        </div>
      ))}
    </div>
  );
}
