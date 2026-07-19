"use client";

/**
 * Opens exactly one URL per click. Plain stacked `<a target="_blank">`
 * lists were opening multiple tabs when hit-targets overlapped or the
 * click bubbled through nearby links.
 */
export function ExternalLink({
  href,
  children,
  className,
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
}) {
  if (!href) return null;

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={className}
      onClick={(e) => {
        e.stopPropagation();
        // Prevent any parent <Link>/card handler from also navigating.
        e.nativeEvent.stopImmediatePropagation?.();
      }}
    >
      {children}
    </a>
  );
}

export function dedupeUrls(urls: (string | undefined | null)[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const u of urls) {
    if (!u || seen.has(u)) continue;
    seen.add(u);
    out.push(u);
  }
  return out;
}
