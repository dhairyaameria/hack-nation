import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { getFounderProfile, getNetworkGraphSeed } from "@/lib/api/client";
import { GenomeRadar } from "@/components/founder/GenomeRadar";
import { ScoreTrendChart } from "@/components/founder/ScoreTrendChart";
import { NetworkBadge } from "@/components/founder/NetworkBadge";
import { FounderNetworkGraph } from "@/components/network/FounderNetworkGraph";
import { MarkdownBrief } from "@/components/company/MarkdownBrief";
import { RefreshFounderButton } from "@/components/founder/RefreshFounderButton";
import { AutoEnrichFounder } from "@/components/founder/AutoEnrichFounder";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";

export const dynamic = "force-dynamic";

function hostLabel(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export default async function FounderProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const founder = await getFounderProfile(id, { enrich: false });
  if (!founder) notFound();

  const networkData = await getNetworkGraphSeed(id);
  const enrichment = founder.enrichment || {};
  const summary = enrichment.summary || "";
  const citations = enrichment.citations || [];
  const webResults = enrichment.web_results || [];
  const scoreDisplay =
    founder.founder_score != null ? Math.round(founder.founder_score * 100) : null;

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <Link
        href="/founders"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Founder Book
      </Link>

      <header className="flex flex-col gap-5 border-b border-border pb-6 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">{founder.display_name}</h1>
          {founder.location && (
            <p className="text-sm text-muted-foreground">{founder.location}</p>
          )}
          <RefreshFounderButton founderId={id} />
          {!summary ? <AutoEnrichFounder founderId={id} /> : null}
        </div>

        <div className="shrink-0 rounded-xl border border-border bg-card px-6 py-4 text-center sm:min-w-[140px]">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Founder Score
          </p>
          <p className="mt-1 text-5xl font-bold tabular-nums tracking-tight text-foreground">
            {scoreDisplay != null ? scoreDisplay : "—"}
          </p>
          <div className="mt-2 flex items-center justify-center gap-2">
            {founder.founder_score_trend && (
              <Badge variant="outline">{founder.founder_score_trend}</Badge>
            )}
            {founder.genome?.execution_velocity?.confidence != null && (
              <span className="text-[11px] text-muted-foreground">
                conf {Math.round((founder.genome.execution_velocity.confidence as number) * 100)}%
              </span>
            )}
          </div>
        </div>
      </header>

      <section className="rounded-xl border border-border bg-background p-6">
        <div className="mb-4 flex items-baseline justify-between gap-3">
          <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Founder brief
          </h2>
          {enrichment.sources?.length ? (
            <span className="text-[11px] text-muted-foreground">
              via {enrichment.sources.join(" · ")}
            </span>
          ) : null}
        </div>
        {summary ? (
          <MarkdownBrief content={summary} citations={citations} />
        ) : (
          <p className="text-sm text-muted-foreground">
            No research brief yet. Use Refresh research or Source founders from the Founder Book.
          </p>
        )}
        {enrichment.disclaimer && (
          <p className="mt-5 border-t border-border pt-4 text-xs leading-relaxed text-muted-foreground">
            {enrichment.disclaimer}
          </p>
        )}
      </section>

      {(citations.length > 0 || webResults.length > 0) && (
        <section className="rounded-xl border border-border bg-background p-6">
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Sources
          </h2>
          <ol className="space-y-3">
            {citations.map((url, i) => (
              <li key={url} className="flex gap-3 text-sm">
                <span className="mt-0.5 w-5 shrink-0 font-mono text-[11px] text-muted-foreground">
                  [{i + 1}]
                </span>
                <a
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  className="min-w-0 text-brand-ink hover:underline"
                >
                  <span className="inline-flex items-center gap-1 font-medium text-foreground">
                    {hostLabel(url)}
                    <ExternalLink className="h-3 w-3" />
                  </span>
                  <span className="mt-0.5 block truncate text-xs text-muted-foreground">{url}</span>
                </a>
              </li>
            ))}
          </ol>
          {webResults.length > 0 && (
            <div className="mt-6 space-y-3 border-t border-border pt-5">
              <h3 className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                Web research
              </h3>
              <ul className="space-y-3">
                {webResults.map((r) => (
                  <li key={r.url} className="text-sm">
                    <a
                      href={r.url}
                      target="_blank"
                      rel="noreferrer"
                      className="font-medium text-foreground hover:underline"
                    >
                      {r.title || hostLabel(r.url || "")}
                    </a>
                    {r.snippet && (
                      <p className="mt-0.5 leading-relaxed text-muted-foreground">{r.snippet}</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

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
          <NetworkBadge proximity={founder.network_proximity ?? null} />
        </div>
      </section>

      <Separator />

      <section>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-2">
          Network Graph
        </h2>
        <FounderNetworkGraph founderId={id} data={networkData as never} />
      </section>

      {(founder.domain_affinity?.length ?? 0) > 0 && (
        <>
          <Separator />
          <section>
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-2">
              Domain Affinity
            </h2>
            <div className="flex flex-wrap gap-2">
              {founder.domain_affinity!.map((d, i) => (
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
