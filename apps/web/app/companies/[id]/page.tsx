import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ExternalLink, FileText } from "lucide-react";
import { deckAbsoluteUrl, getCompanyProfile } from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";
import { AnalyzeButton } from "@/components/opportunity/AnalyzeButton";
import { MarkdownBrief } from "@/components/company/MarkdownBrief";
import { CompanyLogo } from "@/components/company/CompanyLogo";
import { plainSnippet } from "@/lib/utils";

export const dynamic = "force-dynamic";

function hostLabel(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

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
  // enrichment.summary is the full brief; description may be a clipped DB preview.
  const summary = enrichment.summary || company.description || "";
  const citations = enrichment.citations || [];
  const webResults = enrichment.web_results || [];
  const primaryOpp = company.primary_opportunity_id;
  const domainHref = company.domain
    ? company.domain.startsWith("http")
      ? company.domain
      : `https://${company.domain}`
    : null;

  return (
    <div className="min-h-full bg-raise/40">
      <div className="mx-auto max-w-6xl space-y-8 p-8">
        <Link
          href="/apply"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to inbound sources
        </Link>

        <header className="flex flex-col gap-5 border-b border-border pb-8 sm:flex-row sm:items-start">
          <CompanyLogo name={company.name} domain={company.domain} className="h-16 w-16" />
          <div className="min-w-0 flex-1 space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-serif text-3xl font-semibold tracking-tight text-foreground">
                {company.name}
              </h1>
              {company.sector && <Badge variant="secondary">{company.sector}</Badge>}
              {company.stage && <Badge variant="outline">{company.stage}</Badge>}
              <Badge variant="outline">Inbound</Badge>
            </div>
            {domainHref && (
              <a
                href={domainHref}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-sm text-brand-ink hover:underline"
              >
                {company.domain?.replace(/^https?:\/\//, "")}
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
            {primaryOpp && (
              <div className="flex flex-wrap items-center gap-3 pt-1">
                <Link
                  href={`/opportunities/${primaryOpp}`}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground no-underline"
                >
                  Open diligence
                </Link>
                <AnalyzeButton opportunityId={primaryOpp} />
              </div>
            )}
          </div>
        </header>

        <div className="grid gap-8 lg:grid-cols-[minmax(0,1.35fr)_minmax(280px,0.85fr)]">
          <div className="space-y-8">
            <section className="rounded-xl border border-border bg-background p-6 sm:p-8">
              <div className="mb-5 flex items-baseline justify-between gap-3">
                <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  Company analysis
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
                  No public profile summary yet. Open diligence and run Analyze to deepen the
                  dossier.
                </p>
              )}

              {enrichment.disclaimer && (
                <p className="mt-6 border-t border-border pt-4 text-xs leading-relaxed text-muted-foreground">
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
                        <span className="font-medium text-foreground">{hostLabel(url)}</span>
                        <span className="mt-0.5 block truncate text-xs text-muted-foreground">
                          {url}
                        </span>
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
                            <p className="mt-0.5 leading-relaxed text-muted-foreground">
                              {plainSnippet(r.snippet, 280)}
                            </p>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </section>
            )}
          </div>

          <aside className="space-y-6 lg:sticky lg:top-8 lg:self-start">
            <section className="overflow-hidden rounded-xl border border-border bg-background">
              <div className="flex items-center gap-2 border-b border-border px-4 py-3">
                <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  Pitch deck
                </h2>
              </div>
              {pdfUrl ? (
                <>
                  <iframe
                    title={`${company.name} pitch deck`}
                    src={`${pdfUrl}#view=FitH`}
                    className="h-[55vh] w-full border-0 bg-muted/20"
                  />
                  <div className="border-t border-border px-4 py-2 text-xs text-muted-foreground">
                    {company.deck_filename || "deck.pdf"}
                  </div>
                </>
              ) : (
                <p className="px-4 py-8 text-sm text-muted-foreground">No deck on file.</p>
              )}
            </section>

            {(company.opportunities || []).length > 0 && (
              <section className="rounded-xl border border-border bg-background p-4">
                <h2 className="mb-3 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  Linked opportunities
                </h2>
                <ul className="space-y-2">
                  {(company.opportunities || []).map((o) => (
                    <li key={o.id}>
                      <Link
                        href={`/opportunities/${o.id}`}
                        className="text-sm text-foreground hover:underline"
                      >
                        {o.source}
                        {o.screen_verdict ? ` · ${o.screen_verdict}` : ""}
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}
