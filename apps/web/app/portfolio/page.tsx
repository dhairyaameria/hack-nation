import Link from "next/link";
import { Briefcase } from "lucide-react";
import { getPortfolio } from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";
import { DiscoveryChannelBadge } from "@/components/ui/ds";

export const dynamic = "force-dynamic";

function formatCheck(usd: number) {
  return `$${Math.round(usd / 1000)}K`;
}

function formatFundedAt(iso: string | null | undefined) {
  if (!iso) return "Date unknown";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

export default async function PortfolioPage() {
  const companies = await getPortfolio();
  const deployed = companies.reduce((sum, c) => sum + (c.check_size_usd || 0), 0);

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Portfolio</h1>
        <p className="text-sm text-muted-foreground">
          Companies the fund has already backed — closed yes decisions from the 24h funnel.
        </p>
        {companies.length > 0 && (
          <p className="text-xs text-muted-foreground pt-1 font-mono">
            {companies.length} compan{companies.length === 1 ? "y" : "ies"} ·{" "}
            {formatCheck(deployed)} deployed
          </p>
        )}
      </header>

      {companies.length === 0 ? (
        <div className="rounded-lg border border-dashed p-10 text-center space-y-2">
          <Briefcase className="h-8 w-8 mx-auto text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No funded companies yet. Close a $100K yes on an opportunity to land it here.
          </p>
        </div>
      ) : (
        <div className="rounded-[2px] border border-line bg-surface">
          <div className="flex items-center justify-between border-b border-line px-5 py-3 font-mono text-[10.5px] uppercase tracking-[0.1em] text-sub">
            <span>Funded companies</span>
            <span>Sorted by decision date</span>
          </div>
          {companies.map((c) => (
            <Link
              key={c.opportunity_id}
              href={`/opportunities/${c.opportunity_id}`}
              className="block border-b border-line2 border-l-2 border-l-transparent px-5 py-5 !text-ink no-underline transition-colors last:border-b-0 hover:border-l-brand hover:bg-raise"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="font-serif text-xl font-semibold">{c.company_name}</span>
                    <Badge variant="outline" className="font-mono text-[10px]">
                      Funded
                    </Badge>
                    {c.discovery_channel && (
                      <DiscoveryChannelBadge channel={c.discovery_channel} />
                    )}
                  </div>
                  <div className="mt-1.5 font-mono text-[11px] text-sub">
                    {c.founder_name}
                    {c.company_sector && <> · {c.company_sector.replace(/_/g, " ")}</>}
                    {c.company_domain && <> · {c.company_domain}</>}
                  </div>
                </div>
                <div className="shrink-0 text-right space-y-1">
                  <div className="font-serif text-lg font-semibold tabular-nums">
                    {formatCheck(c.check_size_usd)}
                  </div>
                  <div className="font-mono text-[10.5px] text-sub">
                    {formatFundedAt(c.funded_at)}
                  </div>
                  {c.thesis_fit_score != null && (
                    <div className="font-mono text-[10.5px] text-sub">
                      FIT {Math.round(c.thesis_fit_score * 100)}%
                    </div>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
