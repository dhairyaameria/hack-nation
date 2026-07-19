import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { getFounderProfile, getNetworkGraphSeed } from "@/lib/api/client";
import { GenomeRadar } from "@/components/founder/GenomeRadar";
import { ScoreTrendChart } from "@/components/founder/ScoreTrendChart";
import { NetworkBadge } from "@/components/founder/NetworkBadge";
import { FounderNetworkGraph } from "@/components/network/FounderNetworkGraph";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";

export const dynamic = "force-dynamic";

export default async function FounderProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const founder = await getFounderProfile(id);
  if (!founder) notFound();

  const networkData = await getNetworkGraphSeed(id);

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to outbound sources
      </Link>

      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{founder.display_name}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Founder Score{" "}
            <span className="font-medium text-foreground">
              {founder.founder_score != null ? Math.round(founder.founder_score * 100) : "unknown"}
            </span>{" "}
            {founder.founder_score_trend && (
              <Badge variant="outline" className="ml-1">{founder.founder_score_trend}</Badge>
            )}
          </p>
        </div>
      </header>

      <Separator />

      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-2">
            Founder Genome
          </h2>
          <GenomeRadar genome={founder.genome} />
        </div>
        <div className="space-y-4">
          <div>
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-2">
              Founder Score History
            </h2>
            <ScoreTrendChart history={founder.founder_score_history} />
          </div>
          <NetworkBadge proximity={founder.network_proximity} />
        </div>
      </section>

      <Separator />

      <section>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-2">
          Network Graph
        </h2>
        <FounderNetworkGraph founderId={id} data={networkData as never} />
      </section>

      {founder.domain_affinity?.length > 0 && (
        <>
          <Separator />
          <section>
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-2">
              Domain Affinity
            </h2>
            <div className="flex flex-wrap gap-2">
              {founder.domain_affinity.map((d: { sector: string; weight: number; evidence_source: string }, i: number) => (
                <Badge key={i} variant="secondary">
                  {d.sector} · {Math.round(d.weight * 100)}% ({d.evidence_source})
                </Badge>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
