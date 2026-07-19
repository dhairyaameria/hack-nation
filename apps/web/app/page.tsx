import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { IntegrationCarousel } from "@/components/landing/IntegrationCarousel";
import { LandingThemeToggle } from "@/components/landing/LandingThemeToggle";

export const metadata: Metadata = {
  title: "Brain Venture — Deploy $100K checks in 24 hours",
  description:
    "Brain Venture sources exceptional founders before they raise, screens on three independent axes, and ships evidence-backed memos with per-claim trust.",
};

const USPS = [
  {
    title: "Outbound before the raise",
    body: "Live connectors on GitHub, Hacker News, arXiv, LinkedIn, Perplexity, and Tavily discover builders before they open a round — scored like an inbound application.",
  },
  {
    title: "Inbound with almost zero friction",
    body: "Deck + company name is enough. We parse claims, screen fast, and enrich from the public web without over-collecting fields.",
  },
  {
    title: "Three axes — never averaged",
    body: "Founder, Market, and Idea-vs-Market stay independent, each with a trend. Disagreement stays visible instead of collapsing into one vanity score.",
  },
  {
    title: "Trust per claim, not per company",
    body: "Every assertion carries evidence, confidence, and validator status. Contradictions surface before they reach the memo.",
  },
  {
    title: "Full investment memo, gaps flagged",
    body: "Required brief sections plus optional diligence blocks. Missing financials or cap table are marked not disclosed — never fabricated.",
  },
  {
    title: "Memory that does not reset",
    body: "Founder Score and fund memory persist across opportunities. Facts, embeddings, and today’s inbound count stay queryable for agents and investors.",
  },
  {
    title: "Network + narrative depth",
    body: "Second-degree proximity paths with mandatory disclosure, plus Wayback narrative drift for cold-start founders with thin public footprints.",
  },
  {
    title: "Decide in the funnel",
    body: "Run analysis → open the memo → approve investment. Closed yes decisions land in Portfolio with SLA timestamps for the 24-hour path.",
  },
] as const;

const TEAM = [
  {
    name: "Dhairya Ameria",
    linkedin: "https://www.linkedin.com/in/dhairyaameria",
    photo: "/team/dhairya.jpg",
  },
  {
    name: "Khaled Hanafi",
    linkedin: "https://www.linkedin.com/in/khaled-hanafi1",
    photo: "/team/khaled.jpg",
  },
  {
    name: "Omar Toufelaz",
    linkedin: "https://www.linkedin.com/in/omar-toufelaz",
    photo: "/team/omar.jpg",
  },
  {
    name: "Armaan Ahmed",
    linkedin: "https://www.linkedin.com/in/armaanmahmed",
    photo: "/team/armaan.jpg",
  },
] as const;

/**
 * Public landing — hero stays one composition; USPs / integrations / team below.
 * App chrome (sidebar) is suppressed for `/` via AppShell.
 */
export default function LandingPage() {
  return (
    <div className="landing min-h-full bg-[var(--landing-bg)] text-[var(--landing-fg)]">
      {/* —— Hero —— */}
      <section className="relative min-h-screen overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 landing-grid opacity-40"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -top-32 right-[-20%] h-[70vh] w-[70vw] rounded-full bg-[var(--landing-green)]/40 blur-[110px] landing-glow"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute bottom-[-30%] left-[-15%] h-[55vh] w-[55vw] rounded-full bg-[var(--landing-green)]/20 blur-[100px] landing-glow-delay"
        />

        <header className="relative z-10 flex items-center justify-between gap-4 px-6 sm:px-10 pt-8">
          <div className="landing-fade">
            <div className="font-serif text-2xl sm:text-3xl tracking-tight text-[var(--landing-fg)]">
              Brain <span className="text-[var(--landing-green)]">Venture</span>
            </div>
          </div>
          <div className="landing-fade-delay flex items-center gap-3 sm:gap-4">
            <LandingThemeToggle />
              <a
                href="#team"
                className="text-sm font-medium text-[var(--landing-muted)] hover:text-[var(--landing-fg)] transition-colors"
              >
                Team
              </a>
          </div>
        </header>

        <div className="relative z-10 flex min-h-[calc(100vh-5.5rem)] flex-col justify-end sm:justify-center px-6 sm:px-10 pb-16 sm:pb-24 pt-20">
          <div className="max-w-3xl space-y-8">
            <h1 className="landing-rise font-serif text-[clamp(2.75rem,7vw,5.25rem)] leading-[1.05] tracking-tight text-[var(--landing-fg)]">
              Deploying{" "}
              <span className="text-[var(--landing-green)]">$100K</span> checks in 24 hours.
            </h1>
            <p className="landing-rise-delay max-w-xl text-base sm:text-lg text-[var(--landing-muted)] leading-relaxed">
              Source founders before they raise. Screen with transparent trust. Decide with a memo
              that shows its gaps.
            </p>
            <div className="landing-rise-delay-2 flex flex-wrap items-center gap-4">
              <Link
                href="/home"
                className="inline-flex items-center justify-center rounded-[2px] bg-[var(--landing-green-solid)] px-6 py-3 text-sm font-semibold !text-white shadow-[0_0_0_1px_var(--landing-green),0_12px_40px_rgba(44,54,48,0.45)] transition-transform hover:scale-[1.02] hover:!text-white"
              >
                Dashboard
              </Link>
              <a
                href="#team"
                className="inline-flex items-center justify-center rounded-[2px] border-2 border-[var(--landing-green)] px-6 py-3 text-sm font-medium text-[var(--landing-green)] transition-colors hover:bg-[var(--landing-green)]/10"
              >
                Meet the team
              </a>
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
              stroke="var(--landing-green)"
              strokeWidth="2.5"
              opacity="0.9"
              className="landing-path"
            />
            <path
              d="M0 360 C 220 300, 320 240, 500 280 S 780 380, 960 300 S 1240 200, 1440 240"
              stroke="var(--landing-green)"
              strokeWidth="1.25"
              opacity="0.35"
              className="landing-path-delay"
            />
          </svg>
        </div>
      </section>

      {/* —— USPs —— */}
      <section className="relative border-t border-[var(--landing-line)] px-6 sm:px-10 py-16 sm:py-24">
        <div className="mx-auto max-w-5xl">
          <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-[var(--landing-green)] mb-3">
            Why Brain Venture
          </p>
          <h2 className="font-serif text-3xl sm:text-4xl tracking-tight text-[var(--landing-fg)] mb-3 max-w-2xl">
            Built for sourcing depth and honest diligence
          </h2>
          <p className="max-w-xl text-[var(--landing-muted)] text-base leading-relaxed mb-12">
            Every capability below is live in the product: connectors, agents, memos, portfolio close,
            and memory the Ask chat can query.
          </p>

          <ul className="grid gap-8 sm:grid-cols-2">
            {USPS.map((usp) => (
              <li key={usp.title} className="space-y-2 border-t border-[var(--landing-line)] pt-5">
                <h3 className="font-serif text-xl tracking-tight text-[var(--landing-fg)]">
                  {usp.title}
                </h3>
                <p className="text-sm leading-relaxed text-[var(--landing-muted)]">{usp.body}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* —— Integrations carousel —— */}
      <section className="relative border-t border-[var(--landing-line)] px-0 py-16 sm:py-20">
        <div className="mx-auto max-w-4xl px-6 sm:px-10">
          <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-[var(--landing-green)] mb-3">
            Live integrations
          </p>
          <h2 className="font-serif text-3xl sm:text-4xl tracking-tight text-[var(--landing-fg)] mb-3">
            Signals in. Bronze out.
          </h2>
          <p className="max-w-xl text-[var(--landing-muted)] text-base leading-relaxed">
            Multiple connectors feed the same screening funnel as an inbound deck.
          </p>
        </div>
        <IntegrationCarousel />
      </section>

      {/* —— Team —— */}
      <section
        id="team"
        className="relative border-t border-[var(--landing-line)] px-6 sm:px-10 py-16 sm:py-24"
      >
        <div className="mx-auto max-w-5xl">
          <h2 className="font-serif text-3xl sm:text-4xl tracking-tight text-[var(--landing-fg)] mb-10">
            Meet the team
          </h2>
          <ul className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {TEAM.map((person) => (
              <li key={person.name} className="space-y-3">
                <a
                  href={person.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group block space-y-3 no-underline"
                >
                  <div className="relative aspect-square w-full max-w-[180px] overflow-hidden rounded-[2px] border border-[var(--landing-line)] bg-[var(--landing-green)]/12 transition-colors group-hover:border-[var(--landing-green)]">
                    <Image
                      src={person.photo}
                      alt={person.name}
                      fill
                      sizes="180px"
                      className="object-cover"
                    />
                  </div>
                  <div>
                    <p className="font-serif text-lg text-[var(--landing-fg)] transition-colors group-hover:text-[var(--landing-green)]">
                      {person.name}
                    </p>
                    <p className="mt-1 font-mono text-[11px] uppercase tracking-[0.08em] text-[var(--landing-muted)]">
                      LinkedIn ↗
                    </p>
                  </div>
                </a>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <footer className="border-t border-[var(--landing-line)] px-6 sm:px-10 py-8">
        <div className="mx-auto max-w-5xl flex flex-wrap items-center justify-between gap-3 font-mono text-[10.5px] uppercase tracking-[0.1em] text-[var(--landing-muted)]">
          <span>Brain Venture</span>
        </div>
      </footer>
    </div>
  );
}
