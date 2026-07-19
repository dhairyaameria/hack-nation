"use client";

import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

function citationHref(citations: string[], marker: string): string | null {
  const n = Number(marker);
  if (!Number.isFinite(n) || n < 1 || n > citations.length) return null;
  return citations[n - 1] ?? null;
}

/** Turn bare [1][2] markers into linked superscripts when we have citation URLs. */
function linkCitations(text: string, citations: string[]): ReactNode[] {
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/);
    if (!m) return <span key={i}>{part}</span>;
    const href = citationHref(citations, m[1]);
    if (!href) {
      return (
        <sup key={i} className="ml-0.5 text-[10px] text-muted-foreground">
          [{m[1]}]
        </sup>
      );
    }
    return (
      <a
        key={i}
        href={href}
        target="_blank"
        rel="noreferrer"
        className="ml-0.5 align-super text-[10px] font-medium text-brand-ink no-underline hover:underline"
        title={href}
      >
        [{m[1]}]
      </a>
    );
  });
}

function withCitations(children: ReactNode, citations: string[]): ReactNode {
  if (!citations.length) return children;
  return (
    <>
      {Array.isArray(children)
        ? children.map((child, i) =>
            typeof child === "string" ? (
              <span key={i}>{linkCitations(child, citations)}</span>
            ) : (
              child
            )
          )
        : typeof children === "string"
          ? linkCitations(children, citations)
          : children}
    </>
  );
}

export function MarkdownBrief({
  content,
  citations = [],
  compact = false,
}: {
  content: string;
  citations?: string[];
  /** Smaller type for drawers / watchlist cards */
  compact?: boolean;
}) {
  const body = compact ? "text-xs" : "text-[15px]";
  const heading = compact
    ? "mt-3 mb-1 text-sm font-semibold tracking-tight text-foreground first:mt-0"
    : "mt-8 mb-2 font-serif text-xl font-semibold tracking-tight text-foreground first:mt-0";
  const subhead = compact
    ? "mt-3 mb-1 text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground"
    : "mt-6 mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground";

  const components: Components = {
    h1: ({ children }) => <h3 className={heading}>{children}</h3>,
    h2: ({ children }) => <h3 className={heading}>{children}</h3>,
    h3: ({ children }) => <h4 className={subhead}>{children}</h4>,
    p: ({ children }) => (
      <p className={`mb-2 leading-relaxed text-foreground/90 ${body}`}>
        {withCitations(children, citations)}
      </p>
    ),
    ul: ({ children }) => (
      <ul className={`mb-3 list-disc space-y-1 pl-4 leading-relaxed text-foreground/90 ${body}`}>
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol className={`mb-3 list-decimal space-y-1 pl-4 leading-relaxed text-foreground/90 ${body}`}>
        {children}
      </ol>
    ),
    li: ({ children }) => <li>{withCitations(children, citations)}</li>,
    strong: ({ children }) => (
      <strong className="font-semibold text-foreground">{children}</strong>
    ),
    a: ({ href, children }) => (
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="text-brand-ink underline-offset-2 hover:underline"
      >
        {children}
      </a>
    ),
    table: ({ children }) => (
      <div className={`my-3 overflow-x-auto rounded-lg border border-border ${compact ? "text-[11px]" : "text-sm"}`}>
        <table className="w-full min-w-[240px] border-collapse text-left">{children}</table>
      </div>
    ),
    thead: ({ children }) => (
      <thead className="bg-muted/60 text-[10px] uppercase tracking-[0.08em] text-muted-foreground">
        {children}
      </thead>
    ),
    th: ({ children }) => (
      <th className="border-b border-border px-2.5 py-2 font-medium">{children}</th>
    ),
    td: ({ children }) => (
      <td className="border-b border-border/70 px-2.5 py-2 align-top text-foreground/90 last:border-0">
        {withCitations(children, citations)}
      </td>
    ),
    tr: ({ children }) => <tr className="odd:bg-background even:bg-muted/20">{children}</tr>,
    hr: () => <hr className="my-4 border-border" />,
  };

  return (
    <div className="markdown-brief">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
