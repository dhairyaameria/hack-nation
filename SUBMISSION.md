# Submission Answers — working draft

**How to use this file**

- Everyone edits directly. Add your initials in brackets when you change something: `[OT]`, `[DA]`, `[KH]`, `[AA]`.
- Each question has a **DRAFT** to react to. Don't start from a blank page, cut and rewrite and disagree.
- Anything marked 🔴 **NEEDS A HUMAN** is a decision or a claim I could not verify from the repo. Do not submit those as-is.
- Keep the binding rules true in the copy: no composite score, per-claim trust, gaps never fabricated.
- The answers are written without em dashes on purpose, since this text gets pasted into a form and read by judges.

**Status:** draft v2, regenerated against the code as of the latest `main`.

**Changed since v1:** ElevenLabs voice input confirmed shipped and moved into the answers. Voice, the invest/decision action, portfolio, company profiles, deck storage, inbound rerank, and the two-way gap classification all added. Deployment is live. Databricks still unresolved. New open item on the product name.

---

## 1. Short Description

> *Suggested length: 2 to 3 sentences.*

**DRAFT**

Brain Venture is a data- and AI-first venture operating system that takes a founder from discovery to a $100K yes/no decision in under 24 hours. It sources founders before they raise, scores every opportunity on three independent axes that are never averaged into a single number, and produces an investment memo where every claim carries its own evidence, confidence, and validation status. Where the evidence runs out, the memo says so instead of guessing.

*Alternative one-liner if the field is short:*
An evidence-first venture OS that sources founders before they fundraise, scores them on three independent axes, and ships a $100K recommendation in 24 hours, with a traceable source behind every claim.

---

## 2. Problem & Challenge

> *What problem does the project solve? What pain point are we addressing?*

**DRAFT**

Early-stage investing has three failures that compound each other.

**You meet founders too late.** By the time a deck lands in your inbox, the round is often competitive or already gone. The strongest signals, like a founder shipping relentlessly on GitHub, a first-author paper, or a hackathon win, are public long before a raise. Nobody is systematically watching them.

**Diligence does not scale, so it gets skipped.** Verifying a deck's claims against filings, references, and the public web takes days of analyst time per company. Under time pressure it collapses into gut feel plus whoever vouched for the founder, which is exactly how bias enters and how cold-start founders with thin networks get filtered out for the wrong reason.

**AI tools make this worse, not better, when they hide uncertainty.** Most "AI for VC" output is a single confident score with no traceable reasoning. An investor cannot audit it, cannot argue with it, and cannot tell the difference between "we verified this" and "the model assumed this." A wrong number delivered confidently is more dangerous than no number at all.

The core challenge is to **make speed and rigour compatible.** Going faster normally means checking less. We wanted the 24-hour decision to be more auditable than a two-week one, not less.

---

## 3. Target Audience

> *Who benefits? Who is the main target group?*

**DRAFT**

**Primary: the solo GP and the early-stage VC analyst.** A small fund with more inbound than analyst hours, competing against larger funds on speed and conviction rather than brand. Every UX decision in the product is made for this person: dense enough to be useful, readable enough to act on.

**Secondary: scouts and accelerator operators**, who screen high volume with almost no analyst support and need a defensible reason for every pass.

**Third-party beneficiary: founders, especially cold-start ones.** Inbound takes a deck and a company name, with no 40-field form. More importantly, absence of signal is scored as unknown and never as bad, so a first-time founder with no network and no press is not silently penalised for it. This is a binding rule in the system rather than a nice-to-have.

🔴 **NEEDS A HUMAN:** if the form asks for market size or user numbers, someone should decide whether we cite the challenge brief's framing or leave it out. We have no real user data.

---

## 4. Solution & Core Features

> *How do we solve the problem? Main functionalities.*

**DRAFT**

The system covers the full funnel, Sourcing to Screening to Diligence to Decision, with a persistent memory layer underneath it.

**Outbound sourcing, before the raise.** Live connectors on GitHub, Hacker News, arXiv, and LinkedIn, plus Perplexity and Tavily for search-grounded research. Candidates land on a watchlist and move through a state machine: discovered, scored, activation-candidate, outreach-sent, applied. Promotion requires corroboration from more than one signal, so a single noisy source cannot manufacture conviction.

**Inbound with near-zero friction.** A deck and a company name. We store the deck, parse it, extract claims, and run a fast thesis screen, while keeping a pointer from every claim back to the slide it came from. A scheduled Perplexity rerank keeps the inbound queue ordered by fit rather than by arrival time.

**Three independent axes, never averaged.** Founder, Market, and Idea-vs-Market are computed, stored, and displayed separately, each with its own trend. There is no composite score anywhere in the UI, the API, or the memo. Disagreement between axes stays visible instead of being smoothed into one misleading number.

**Per-claim trust, not per-company.** An Analyst, Validator, and Referee agent chain cross-checks each claim against independent sources. Contradictions surface explicitly: when a deck claims $1.2M ARR and the Stripe export says $412K, the memo shows both side by side rather than quietly picking one.

**Memos that mark their own gaps.** Required sections, each carrying its evidence. Empty sections are classified rather than blanked: *not disclosed* means the founder withheld it, which is a fact about the process, while *insufficient evidence* means our source pack could not support the section, which is a fact about our coverage. Most tools collapse those two into one blank.

**Decision in the funnel.** Approve an investment directly from the memo. Closed decisions land in Portfolio with SLA timestamps, so the 24-hour claim is measured end to end rather than asserted.

**Persistent memory, shared with agents.** A Founder Score that follows the person across applications and never resets, plus a fact store with validity windows and embeddings. An MCP server exposes the same memory the dashboard uses, so an external AI agent and the UI query one brain instead of two.

**Ask by text or by voice.** A floating assistant answers questions about the pipeline in plain English and returns cited sources, with per-clause match explanations rather than an opaque relevance score. Voice input runs through ElevenLabs transcription.

---

## 5. Unique Selling Proposition

> *What makes this different?*

**DRAFT**

**We refuse to give you one number.** Nearly every competing tool compresses a company into a single score, because a single score demos well. We deliberately do not. Three axes stay independent with independent trends. When the founder is exceptional and the market is weak, that tension is the most valuable thing on the screen, and averaging destroys it.

**Trust attaches to claims, not companies.** "NovaMetrics: 78/100" tells you nothing you can act on. "This ARR figure is contradicted by two independent sources, and here they are" tells you what to ask on the next call.

**Gaps are a feature.** A memo that marks what it does not know is more trustworthy than one that reads as complete, and we treat that as a design principle rather than an apology. The system never fabricates a missing section, and it distinguishes what was withheld from what we could not verify.

**Cold-start founders are first-class.** Absence of network signal is explicitly scored as unknown rather than negative, and network proximity is capped at roughly 10 to 15 percent of the Founder axis with mandatory plain-language disclosure. This is a deliberate counter to the bias that network-driven sourcing normally amplifies.

**Speed that is auditable.** The 24-hour path is instrumented from first signal to decision, and every conclusion along it traces back to a source locator.

---

## 6. Implementation & Technology

> *How did we technically implement it? What technology do we use?*

**DRAFT**

**Frontend.** Next.js 16 with the App Router, React 19, TypeScript, Tailwind v4 driven by a token-based design system, and shadcn/ui primitives. Server components fetch from the API with a fixture fallback, so the dashboard stays demoable when an endpoint is not live. Light and dark themes are fully token-driven with no hardcoded colours.

**Backend.** FastAPI with Pydantic contracts, organised by domain: `ingestion` for deck parsing, connectors, watchlist, and enrichment; `intelligence` for 3-axis scoring, the Analyst/Validator/Referee chain, and memos; `memory` for the fact store, extraction, and embeddings; `agent` for chat and natural-language query; `graphql` for the founder and company graph; and `mcp` for the FastMCP server.

**Data.** Supabase, meaning Postgres with pgvector for embeddings plus Auth and Storage for pitch decks. The schema is managed as ordered SQL migrations, currently twelve, with a Bronze, Silver, and Gold separation between raw ingested records, resolved entities, and computed features. Every ingested record carries provenance: `source`, `source_entity_id`, `fetched_at`, and `run_id`.

**AI and research.** OpenAI for the agent chain, Perplexity for search-grounded research and inbound reranking, Tavily for claim verification, Wayback CDX for narrative drift on founders with thin public footprints, and ElevenLabs for voice transcription in the assistant.

**Agent interface.** A FastMCP server exposes the same memory layer the dashboard reads from, so an external AI agent and the UI query one brain rather than two. This is what makes "ask the fund a question and get cited sources back" work.

**Jobs.** Scheduled pipelines for the daily sourcing sweep and the Perplexity inbound rerank.

**Deployment.** Web on Vercel, API on Render via Docker, both live.

🔴 **NEEDS A HUMAN:** `README.md` still lists **Databricks** in the planned stack, and there is no Databricks code anywhere in the repo. I have re-checked this. Either drop it from the submission and the README, or have whoever planned it explain the intended role. Do not claim it as implemented.

---

## 7. Results & Impact

> *What does the solution bring?*

**DRAFT**

**What works end to end today:** outbound discovery across four connectors feeding a corroboration-gated watchlist; inbound deck intake with storage, claim extraction, fast screening, and Perplexity reranking; 3-axis scoring wired to live models; contradiction detection that surfaces conflicts between a deck and independent sources; evidence-backed memos with classified gaps; an approve-investment action that writes into Portfolio with SLA timestamps; a persistent memory layer queryable by external agents over MCP; and a text-and-voice assistant that answers with citations.

**The impact we are claiming:**

*Time.* Signal to decision compressed from the typical multi-week early-stage process into a measured 24-hour path, with the SLA instrumented rather than asserted.

*Auditability.* Every factual output, whether a memo section, an axis score, or a chat answer, carries a source locator. An investor can challenge a single claim without re-running the whole analysis.

*Reach.* Sourcing that surfaces founders before they open a round, and that does not structurally penalise those without a network.

*Better failure modes.* When the system is uncertain, that uncertainty is visible. The expensive mistake in venture is not a missing data point, it is a confident wrong one.

🔴 **NEEDS A HUMAN. Do not submit numbers we have not measured.** If the form wants quantitative results, we have to run it and record them. In order of how cheaply we can get them honestly:

- Founders surfaced by one real sourcing sweep, and how many passed the corroboration gate.
- Wall-clock time for a single signal to memo to decision run.
- Claims extracted and independently verified on the demo deck, plus contradictions caught.
- Sections filled versus gaps flagged on a generated memo.

These are deliberately blank rather than invented. The whole pitch is that we do not fabricate data, so a made-up metric here is the one thing that could genuinely undermine us.

---

## Open items for the team

| Item | Owner | Status |
|---|---|---|
| Databricks: drop from README and submission, or justify it | | 🔴 open |
| **Product name: the UI says "Brain Venture", the README and Render service say "VC Brain". Pick one before submitting.** | | 🔴 open |
| Run one timed end-to-end pass and record real numbers for §7 | | 🔴 open |
| Add live demo URLs (Vercel web, Render API) if the form asks | | 🔴 open |
| Confirm team affiliations if the form asks for them | | 🔴 open |
| Final read-through for tone and per-field length limits | | 🔴 open |
| ~~Confirm ElevenLabs shipped~~ | | ✅ shipped, in §4 and §6 |
