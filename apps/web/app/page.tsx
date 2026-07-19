import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "VC Brain — Maschmeyer Group",
  description: "Find exceptional founders. Deploy $100K checks in 24 hours.",
};

const SOURCE_INTEGRATIONS = [
  {
    name: "GitHub",
    role: "Builder velocity",
    detail: "Repos, stars, recent pushes, and public shipping cadence.",
  },
  {
    name: "Hacker News",
    role: "Launch traction",
    detail: "Story points, comments, and early community signal via Algolia.",
  },
  {
    name: "arXiv",
    role: "Technical depth",
    detail: "Papers and research footprint for technical founders.",
  },
  {
    name: "LinkedIn",
    role: "Public footprint",
    detail: "Public /in profiles via web search — identity signal, not a private API scrape.",
  },
  {
    name: "Perplexity",
    role: "Live research",
    detail: "Thesis-grounded web research with native citations into Bronze.",
  },
  {
    name: "Tavily",
    role: "Web corroboration",
    detail: "Independent search to verify claims — never fabricate from silence.",
  },
] as const;

/**
 * Public landing — hero stays one composition; integrations live below the fold.
 * App chrome (sidebar) is suppressed for `/` via AppShell.
 */
export default function LandingPage() {
  return (
    <div className="landing bg-[var(--ink)] text-[var(--raise)]">
      {/* —— Hero —— */}
      <section className="relative min-h-screen overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 landing-grid opacity-[0.35]"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -top-32 right-[-20%] h-[70vh] w-[70vw] rounded-full bg-[var(--brand)]/25 blur-[120px] landing-glow"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute bottom-[-30%] left-[-15%] h-[55vh] w-[55vw] rounded-full bg-[var(--raise)]/10 blur-[100px] landing-glow-delay"
        />

        <header className="relative z-10 flex items-center justify-between px-6 sm:px-10 pt-8">
          <div className="landing-fade">
            <div className="font-serif text-2xl sm:text-3xl tracking-tight text-[var(--raise)]">
              VC Brain
            </div>
            <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-[var(--faint)] mt-1">
              Maschmeyer Group
            </div>
          </div>
          <Link
            href="/outbound"
            className="landing-fade-delay text-sm font-medium text-[var(--raise)]/80 hover:text-[var(--raise)] transition-colors"
          >
           Dashboard
          </Link>
        </header>

        <div className="relative z-10 flex min-h-[calc(100vh-5.5rem)] flex-col justify-end sm:justify-center px-6 sm:px-10 pb-16 sm:pb-24 pt-20">
          <div className="max-w-3xl space-y-8">
            <h1 className="landing-rise font-serif text-[clamp(2.75rem,7vw,5.25rem)] leading-[1.05] tracking-tight text-[var(--raise)]">
              Deploying $100K checks in 24 hours.
            </h1>
            <p className="landing-rise-delay max-w-xl text-base sm:text-lg text-[var(--faint)] leading-relaxed">
              Find exceptional founders before they raise — source, screen, and diligence through one
              evidence-backed operating system.
            </p>
            <div className="landing-rise-delay-2 flex flex-wrap items-center gap-4">
              <Link
                href="/outbound"
                className="inline-flex items-center justify-center bg-[var(--brand)] px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-[var(--brand-ink)]"
              >
                Open Outbound Sources
              </Link>
              <Link
                href="/apply"
                className="inline-flex items-center justify-center border border-[var(--line3)] px-6 py-3 text-sm font-medium text-[var(--raise)] transition-colors hover:border-[var(--faint)] hover:bg-white/5"
              >
                Inbound application
              </Link>
            </div>
          </div>
        </div>

        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 bottom-0 h-[42vh] sm:h-[48vh]"
        >
          <svg
            className="h-full w-full"
            viewBox="0 0 1440 420"
            preserveAspectRatio="none"
            fill="none"
          >
            <path
              d="M0 320 C 180 280, 260 180, 420 200 S 700 340, 880 260 S 1200 120, 1440 160"
              stroke="var(--brand)"
              strokeWidth="1.5"
              opacity="0.55"
              className="landing-path"
            />
            <path
              d="M0 360 C 220 300, 320 240, 500 280 S 780 380, 960 300 S 1240 200, 1440 240"
              stroke="var(--raise)"
              strokeWidth="1"
              opacity="0.2"
              className="landing-path-delay"
            />
          </svg>
        </div>
      </section>

      {/* —— Source integrations (below the fold) —— */}
      <section className="relative border-t border-[var(--line3)]/30 px-6 sm:px-10 py-20 sm:py-28">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-[var(--brand)] mb-3">
            Live integrations
          </p>
          <h2 className="font-serif text-3xl sm:text-4xl tracking-tight text-[var(--raise)] mb-4">
            Every outbound signal lands in Bronze.
          </h2>
          <p className="max-w-xl text-[var(--faint)] text-base leading-relaxed mb-14">
            Six live connectors score candidates the same way as an inbound deck — multi-signal
            corroboration required, cold start never penalized.
          </p>

          <ul className="divide-y divide-[var(--line3)]/25">
            {SOURCE_INTEGRATIONS.map((source, i) => (
              <li
                key={source.name}
                className="landing-integ grid grid-cols-1 sm:grid-cols-[8rem_10rem_1fr] gap-2 sm:gap-8 py-6 items-baseline"
                style={{ animationDelay: `${0.08 * i}s` }}
              >
                <span className="font-serif text-xl text-[var(--raise)]">{source.name}</span>
                <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-[var(--brand)]">
                  {source.role}
                </span>
                <span className="text-sm text-[var(--faint)] leading-relaxed">{source.detail}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
