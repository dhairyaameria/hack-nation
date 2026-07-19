import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { deckAbsoluteUrl, getCompanyProfile } from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { AnalyzeButton } from "@/components/opportunity/AnalyzeButton";

export const dynamic = "force-dynamic";

export default async function CompanyProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const company = await getCompanyProfile(id);
  if (!company) notFound();

  const pdfUrl = deckAbsoluteUrl(company.deck_url);
  const enrichment = company.enrichment || {};
  const citations = enrichment.citations || [];
  const webResults = enrichment.web_results || [];
  const primaryOpp = company.primary_opportunity_id;

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <Link
        href="/apply"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to inbound sources
      </Link>

      <header className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-3xl font-semibold tracking-tight">{company.name}</h1>
          {company.sector && <Badge variant="secondary">{company.sector}</Badge>}
          {company.stage && <Badge variant="outline">{company.stage}</Badge>}
        </div>
        {company.domain && (
          <a
            href={company.domain.startsWith("http") ? company.domain : `https://${company.domain}`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-sm text-brand-ink hover:underline"
          >
            {company.domain}
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        )}
        <p className="text-sm text-muted-foreground max-w-3xl leading-relaxed whitespace-pre-wrap">
          {company.description || enrichment.summary || "No public profile summary yet."}
        </p>
        {enrichment.disclaimer && (
          <p className="text-xs text-muted-foreground/80">{enrichment.disclaimer}</p>
        )}
      </header>

      {primaryOpp && (
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={`/opportunities/${primaryOpp}`}
            className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium no-underline"
          >
            Open diligence
          </Link>
          <AnalyzeButton opportunityId={primaryOpp} />
        </div>
      )}

      <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Pitch deck
          </h2>
          {pdfUrl ? (
            <div className="overflow-hidden rounded-xl border bg-muted/20">
              <iframe
                title={`${company.name} pitch deck`}
                src={`${pdfUrl}#view=FitH`}
                className="h-[70vh] w-full border-0"
              />
              <div className="border-t px-3 py-2 text-xs text-muted-foreground">
                {company.deck_filename || "deck.pdf"}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No deck on file for this company.</p>
          )}
        </section>

        <section className="space-y-6">
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              Sources
            </h2>
            {citations.length === 0 && webResults.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No research citations yet. Open diligence and run Analyze to deepen the dossier.
              </p>
            ) : (
              <ul className="space-y-2">
                {citations.slice(0, 10).map((url) => (
                  <li key={url}>
                    <a
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm text-brand-ink hover:underline break-all"
                    >
                      {url}
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {webResults.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                Web research
              </h2>
              <ul className="space-y-3">
                {webResults.map((r) => (
                  <li key={r.url} className="text-sm">
                    <a
                      href={r.url}
                      target="_blank"
                      rel="noreferrer"
                      className="font-medium text-foreground hover:underline"
                    >
                      {r.title || r.url}
                    </a>
                    {r.snippet && (
                      <p className="mt-0.5 text-muted-foreground leading-relaxed">{r.snippet}</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <Separator />

          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              Linked opportunities
            </h2>
            <ul className="space-y-2">
              {(company.opportunities || []).map((o) => (
                <li key={o.id}>
                  <Link
                    href={`/opportunities/${o.id}`}
                    className="text-sm hover:underline"
                  >
                    {o.company_name} — {o.source}
                    {o.screen_verdict ? ` (${o.screen_verdict})` : ""}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}
