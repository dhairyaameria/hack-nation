"use client";

const INTEGRATIONS = [
  { name: "GitHub", mark: GitHubMark },
  { name: "Hacker News", mark: HackerNewsMark },
  { name: "arXiv", mark: ArxivMark },
  { name: "LinkedIn", mark: LinkedInMark },
  { name: "Perplexity", mark: PerplexityMark },
  { name: "Tavily", mark: TavilyMark },
] as const;

/** Fast looping logo strip — duplicated track for seamless marquee. */
export function IntegrationCarousel() {
  const track = [...INTEGRATIONS, ...INTEGRATIONS, ...INTEGRATIONS];

  return (
    <div className="landing-marquee relative mt-12 overflow-hidden py-2">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 bg-gradient-to-r from-[var(--landing-bg)] to-transparent sm:w-28"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-gradient-to-l from-[var(--landing-bg)] to-transparent sm:w-28"
      />
      <div className="landing-marquee-track flex w-max items-center gap-10 sm:gap-14">
        {track.map((item, i) => {
          const Mark = item.mark;
          return (
            <div
              key={`${item.name}-${i}`}
              className="flex shrink-0 items-center gap-3 text-[var(--landing-green)]"
            >
              <Mark className="h-8 w-8 sm:h-9 sm:w-9" />
              <span className="font-serif text-xl sm:text-2xl tracking-tight text-[var(--landing-fg)]">
                {item.name}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function GitHubMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden>
      <path d="M12 .3C5.37.3 0 5.67 0 12.3c0 5.3 3.44 9.8 8.2 11.39.6.11.82-.26.82-.58v-2.02c-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.33-1.76-1.33-1.76-1.09-.74.08-.73.08-.73 1.2.09 1.84 1.24 1.84 1.24 1.07 1.83 2.8 1.3 3.49.99.11-.78.42-1.3.76-1.6-2.66-.3-5.46-1.33-5.46-5.93 0-1.31.47-2.38 1.24-3.22-.12-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.29-1.55 3.3-1.23 3.3-1.23.66 1.66.24 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.8 5.62-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.82.58A12 12 0 0 0 24 12.3C24 5.67 18.63.3 12 .3z" />
    </svg>
  );
}

function HackerNewsMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden>
      <path d="M0 0v24h24V0H0zm13.3 13.6L17.7 5h-2.2l-3.1 6.1L9 5H6.7l4.5 8.6v5.1h2.1v-5.1z" />
    </svg>
  );
}

function ArxivMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden>
      <rect x="2" y="3" width="20" height="18" rx="2" stroke="currentColor" strokeWidth="1.8" />
      <path
        d="M7 15.5V8.5h2.2c1.4 0 2.3.8 2.3 2s-.9 2-2.3 2H8.2v3H7zm1.2-4.2h.9c.6 0 1-.3 1-.9s-.4-.9-1-.9h-.9v1.8zM13.5 15.5l2.1-7h1.4l2.1 7h-1.3l-.4-1.4h-2.2l-.4 1.4h-1.3zm2.3-2.5h1.4l-.7-2.4-.7 2.4z"
        fill="currentColor"
      />
    </svg>
  );
}

function LinkedInMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden>
      <path d="M20.45 20.45h-3.55v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.47-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.8 0 0 .77 0 1.73v20.54C0 23.23.8 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z" />
    </svg>
  );
}

function PerplexityMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden>
      <path d="M12 2 4.5 6.5v5.8L12 17l7.5-4.7V6.5L12 2zm0 2.3 5.2 3.1v3.7L12 14.3 6.8 11.1V7.4L12 4.3zM4.5 14.2v3.3L12 22l7.5-4.5v-3.3L12 18.7l-7.5-4.5z" />
    </svg>
  );
}

function TavilyMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden>
      <circle cx="11" cy="11" r="6.5" stroke="currentColor" strokeWidth="1.8" />
      <path d="M16 16l5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="11" cy="11" r="2.2" fill="currentColor" />
    </svg>
  );
}
