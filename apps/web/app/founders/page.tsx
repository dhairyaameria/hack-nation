import Link from "next/link";
import { getFounders } from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";
import { FounderSourcePanel } from "@/components/founder/FounderSourcePanel";

export const dynamic = "force-dynamic";

function scoreLabel(score: number | null | undefined): string {
  if (score == null) return "—";
  return String(Math.round(score * 100));
}

export default async function FoundersPage() {
  const founders = await getFounders();

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Founder Book</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Sourced and enriched founders with persistent Founder Scores.
        </p>
      </header>

      <FounderSourcePanel />

      {founders.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No founders yet. Run a founder sweep or research a name above.
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {founders.map((f) => (
            <Link
              key={f.id}
              href={`/founders/${f.id}`}
              className="block rounded-xl bg-card py-4 text-sm text-card-foreground ring-1 ring-foreground/10 hover:shadow-md transition-shadow px-4"
            >
              <div className="flex items-start justify-between gap-3 pb-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold truncate">{f.display_name}</h3>
                    {f.source && (
                      <Badge variant={f.source === "outbound" ? "secondary" : "outline"}>
                        {f.source}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground mt-0.5">
                    {f.company_name || "Company unknown"}
                  </p>
                </div>
                <div className="shrink-0 text-right">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                    Score
                  </p>
                  <p className="text-2xl font-bold tabular-nums tracking-tight text-foreground">
                    {scoreLabel(f.founder_score)}
                  </p>
                </div>
              </div>
              {f.has_enrichment && (
                <p className="text-[11px] text-muted-foreground">Research brief on file</p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
