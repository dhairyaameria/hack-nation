import Link from "next/link";
import { getPipelineDashboard } from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";

export const dynamic = "force-dynamic";

export default async function FoundersPage() {
  const dashboard = await getPipelineDashboard();
  const founders = Array.from(
    new Map(
      dashboard.opportunities.map((o) => [
        o.founder_id,
        { id: o.founder_id, name: o.founder_name, company: o.company_name, source: o.source },
      ])
    ).values()
  );

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Founder Book</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {founders.map((f) => (
          <Link
            key={f.id}
            href={`/founders/${f.id}`}
            className="block rounded-xl bg-card py-4 text-sm text-card-foreground ring-1 ring-foreground/10 hover:shadow-md transition-shadow px-4"
          >
            <div className="flex items-center gap-2 pb-2">
              <h3 className="font-semibold">{f.name}</h3>
              <Badge variant={f.source === "outbound" ? "secondary" : "outline"}>
                {f.source}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">{f.company}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
