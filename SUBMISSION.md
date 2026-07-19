# Submission Answers — working draft

**How to use this file**

- Everyone edits directly. Add your initials in brackets when you change something: `[OT]`, `[DA]`, `[KH]`, `[AA]`.
- Each question has a **DRAFT** to react to. Don't start from a blank page — cut, rewrite, disagree.
- Anything marked 🔴 **NEEDS A HUMAN** is a claim I could not verify from the repo. Do not submit those as-is.
- Keep the binding rules of the project true in the copy: no composite score, per-claim trust, gaps never fabricated.

**Status:** draft v1, generated from `README.md`, `docs/00-OVERVIEW.md`, `VC_Brain_PRD.md`, and the actual code in `apps/`.

---

## 1. Short Description

> *Suggested length: 2–3 sentences.*

**DRAFT**

Brain Venture is a data- and AI-first venture operating system that takes a founder from discovery to a $100K yes/no decision in under 24 hours. It sources founders *before* they raise, scores every opportunity on three independent axes that are never averaged into one number, and produces an investment memo where every claim carries its own evidence, confidence, and validation status. Where the evidence runs out, the memo says so instead of guessing.

*Alternative one-liner if the field is short:*
An evidence-first venture OS: sources founders before they fundraise, scores them on three independent axes, and ships a $100K recommendation in 24 hours — with a traceable source behind every claim.

---

## 2. Problem & Challenge

> *What problem does the project solve? What pain point are we addressing?*

**DRAFT**

Early-stage investing has three failures that compound each other:

**You meet founders too late.** By the time a deck lands in your inbox, the round is often competitive or gone. The strongest signals — a founder shipping relentlessly on GitHub, a first-author paper, a hackathon win — are public long before a raise, but nobody is systematically watching them.

**Diligence does not scale, so it gets skipped.** Verifying a deck's claims against filings, references, and the public web takes days of analyst time per company. Under time pressure it collapses into gut feel plus whoever vouched for the founder — which is exactly how bias enters and how cold-start founders with thin networks get filtered out for the wrong reason.

**AI tools make this worse, not better, when they hide uncertainty.** Most "AI for VC" output is a single confident score with no traceable reasoning. An investor cannot audit it, cannot argue with it, and cannot tell the difference between *"we verified this"* and *"the model assumed this."* A wrong number delivered confidently is more dangerous than no number.

The core challenge: **make speed and rigour compatible.** Going faster usually means checking less. We wanted the 24-hour decision to be *more* auditable than a two-week one, not less.

---

## 3. Target Audience

> *Who benefits? Who is the main target group?*

**DRAFT**

**Primary — the solo GP and the early-stage VC analyst.** A small fund with more inbound than analyst hours, competing against bigger funds on speed and conviction rather than brand. Every UX decision in the product is made for this person: dense enough to be useful, readable enough to act on.

**Secondary — scouts and accelerator operators**, who screen high volume with almost no analyst support and need a defensible reason for every pass.

**Third-party beneficiary — founders, especially cold-start ones.** Inbound takes a deck and a company name; no 40-field form. More importantly, absence of signal is scored as *unknown*, never as *bad* — so a first-time founder with no network and no press is not silently penalised for it. This is a binding rule in the system, not a nice-to-have.

🔴 **NEEDS A HUMAN:** if the submission asks for market size or user numbers, someone should decide whether we cite the challenge brief's framing or leave it out. I have no real user data.

---

## 4. Solution & Core Features

> *How do we solve the problem? Main functionalities.*

**DRAFT**

The system covers the full funnel — **Sourcing → Screening → Diligence → Decision** — with memory underneath it.

**Outbound sourcing (before the raise).** Live connectors on GitHub, Hacker News, arXiv, and LinkedIn, plus Perplexity and Tavily for search-grounded research. Candidates land on a watchlist and move through a state machine (`discovered → scored → activation-candidate → outreach-sent → applied`). Promotion requires corroboration from more than one signal, so a single noisy source cannot manufacture conviction.

**Inbound with near-zero friction.** A deck and a company name. We parse the deck, extract claims, and run a fast thesis screen — while keeping a pointer from every claim back to the slide it came from.

**Three independent axes, never averaged.** Founder, Market, and Idea-vs-Market are computed, stored, and displayed separately, each with its own trend. There is no composite score anywhere in the UI, API, or memo. Disagreement between axes stays visible instead of being smoothed into one misleading number.

**Per-claim trust, not per-company.** An Analyst → Validator → Referee agent chain cross-checks each claim against independent sources. Contradictions are surfaced explicitly: when a deck claims $1.2M ARR and the Stripe export says $412K, the memo shows both side by side rather than picking one.

**Memos that mark their own gaps.** Required sections, each carrying its evidence. Missing data is flagged, and we distinguish two different things that most tools collapse: *not disclosed* (the founder withheld it — a fact about the process) versus *unknown* (we searched and could not confirm — a fact about our coverage).

**Persistent memory.** A Founder Score that follows the person across applications and never resets, plus a fact store with validity windows and embeddings, queryable by both the dashboard and external agents over MCP.

**24-hour SLA instrumentation.** Timestamps from first signal to decision, so the speed claim is measured rather than asserted.

---

## 5. Unique Selling Proposition

> *What makes this different?*

**DRAFT**

**We refuse to give you one number.** Nearly every competing tool compresses a company into a single score, because a single score demos well. We deliberately do not: three axes stay independent with independent trends. When the founder is exceptional and the market is weak, that tension is the most valuable thing on the screen, and averaging destroys it.

**Trust attaches to claims, not companies.** "NovaMetrics: 78/100" tells you nothing you can act on. "This ARR figure is contradicted by two independent sources, and here they are" tells you what to ask on the next call.

**Gaps are a feature.** A memo that marks what it does not know is more trustworthy than one that reads as complete, and we treat that as a design principle rather than an apology. The system never fabricates a missing section, and it distinguishes withheld from unverified.

**Cold-start founders are first-class.** Absence of network signal is explicitly scored as unknown rather than negative, and network proximity is capped at roughly 10–15% of the Founder axis with mandatory plain-language disclosure. This is a direct, deliberate counter to the bias that network-driven sourcing normally amplifies.

**Speed that is auditable.** The 24-hour decision is instrumented end to end, and every conclusion in it can be traced back to a source locator.

---

## 6. Implementation & Technology

> *How did we technically implement it? What technology do we use?*

**DRAFT**

**Frontend.** Next.js 16 (App Router, React 19, TypeScript), Tailwind v4 with a token-driven design system, shadcn/ui primitives. Server components fetch from the API with a fixture fallback, so the dashboard stays demoable when a backend endpoint is not live. Light and dark themes are token-based; no hardcoded colours.

**Backend.** FastAPI (Python) with Pydantic contracts, organised by domain: `ingestion` (deck parsing, connectors, watchlist, enrichment), `intelligence` (3-axis scoring, Analyst/Validator/Referee, memos), `memory` (fact store, extraction, embeddings), `agent` (chat, NL query), `graphql` (founder/company graph), and `mcp` (FastMCP server).

**Data.** Supabase — Postgres with pgvector for embeddings, plus Auth and Storage for pitch decks. Schema is managed as ordered SQL migrations (currently 012), with a Bronze/Silver/Gold separation between raw ingested records, resolved entities, and computed features. Every ingested record carries provenance: `source`, `source_entity_id`, `fetched_at`, `run_id`.

**AI and research.** OpenAI for the agent chain, Perplexity for search-grounded research and inbound reranking, Tavily for claim verification, Wayback CDX for narrative drift on founders with thin public footprints.

**Agent interface.** A FastMCP server exposes the same memory the dashboard uses, so an external AI agent and the UI query one brain rather than two — this is what makes "ask the fund a question and get cited sources back" work.

**Jobs.** Scheduled pipelines for the daily sourcing sweep and the Perplexity inbound rerank.

**Deployment.** Vercel (web) and Render/Docker (API).

🔴 **NEEDS A HUMAN:** `README.md` lists **Databricks** in the planned stack, but there is no Databricks code in the repo. Either drop it from the submission or have whoever planned it explain the intended role — do not claim it as implemented.

🔴 **NEEDS A HUMAN:** ElevenLabs voice briefing is listed as a planned flourish. Confirm whether it shipped before mentioning it.

---

## 7. Results & Impact

> *What does the solution bring?*

**DRAFT**

**What works end to end today:** outbound discovery across four connectors into a corroboration-gated watchlist; inbound deck intake with claim extraction and fast screening; 3-axis scoring wired to live models; contradiction detection surfacing conflicts between a deck and independent sources; evidence-backed memos with explicit gap flags; a persistent memory layer queryable by agents over MCP; and a dashboard covering the full funnel from sourcing to portfolio.

**The impact we are claiming:**

*Time.* Signal to decision compressed from the typical multi-week early-stage process to a measured 24-hour path, with the SLA instrumented rather than asserted.

*Auditability.* Every factual output — memo section, axis score, chat answer — carries a source locator. An investor can challenge any single claim without re-doing the whole analysis.

*Reach.* Sourcing that surfaces founders before they open a round, and that does not structurally penalise those without a network.

*Better failure modes.* When the system is uncertain, that is visible. The expensive mistake in venture is not a missing data point, it is a confident wrong one.

🔴 **NEEDS A HUMAN — do not submit numbers we have not measured.** If the form wants quantitative results, we need to actually run and record them. Candidates, in order of how cheaply we can get them honestly:

- Number of founders surfaced by a real sourcing sweep, and how many passed the corroboration gate.
- Wall-clock time for one full signal → memo → decision run.
- Claims extracted and independently verified on the demo deck, plus contradictions caught.
- Sections filled vs. gaps flagged on a generated memo.

I have deliberately left these blank rather than invent them. Given the whole pitch is "we do not fabricate data," a made-up metric in the submission is the one thing that could genuinely undermine us.

---

## Open items for the team

| Item | Owner | Status |
|---|---|---|
| Decide whether Databricks stays in the stack description | | 🔴 open |
| Confirm ElevenLabs shipped or drop it | | 🔴 open |
| Run one timed end-to-end pass and record real numbers for §7 | | 🔴 open |
| Agree the affiliations on the landing page team section | | 🔴 open |
| Final read-through for tone and length limits per field | | 🔴 open |
