# 04 — Intelligence, Trust & Memos (Agent C)

**Owner:** Agent C — Intelligence
**Depends on:** Agent A's Gold features + claims/evidence tables; Agent B's ingested data.
**PRD sections covered:** §7.6, §7.7, §8, §11 (all), §12.1, §12.2, §13.1, §13.3.

---

## Mission

The reasoning layer: 3-axis scoring, the Analyst→Validator→Referee agent pipeline, per-claim Trust Scores, evidence-backed memos, full agentic traceability, and the confidence-interval research track.

## 1. Multi-Axis Screening (never averaged — hard rule)

Three independent axes per opportunity, each with value + trend + confidence + evidence:
- **Founder axis:** track record, technical depth proxies, execution velocity, resilience proxies, founder-market fit, persistent Founder Score (input, not substitute), capped network_embeddedness sub-signal (from Agent B, max ~10-15%, separately labeled).
- **Market axis:** TAM/SAM/SOM signals, competitive density, timing → rated `bullish | neutral | bear`.
- **Idea-vs-Market axis:** does the idea survive scrutiny as-is, or is the team strong enough to pivot? Distinct judgment from Market.

Trends (`improving|stable|declining`) computed from axis history in Memory. Axis scores write back into Memory (founder history, market comparables corpus, idea-pattern corpus).

## 2. Multi-Agent Pipeline

1. **Primary Analyst Agent** (OpenAI, structured outputs): drafts claims, axis scores, first memo pass from Memory data. Bull-case framing.
2. **Validator Agent** (Stretch Goal 2): cross-checks every claim against Tavily/Perplexity retrieval, comparable rounds/market references, internal consistency (including Wayback-vs-current contradictions from Agent B). Bear-case framing. Output per claim: `status` (`verified|contradicted|weakly_supported|unknown`), `confidence_delta`, `contradiction_reason`, `required_followup`.
3. **Referee Agent:** resolves Analyst/Validator disagreement, produces final calibrated memo + axis scores + recommendation.

Rules:
- ALL claims pass validation before memo publish. Contradicted claims are removed or explicitly flagged — never silently passed.
- The Bull/Bear disagreement is preserved and displayable (feeds the demo).

## 3. Trust Layer

- Trust Score per claim = f(source reliability, corroboration count, recency, validator outcome).
- `claim_evidence_links` with `supports`/`contradicts` relations.
- Contradictions surface to the investor BEFORE the final memo.

## 4. Agentic Traceability (Stretch Goal 1 — highest-leverage per the brief)

- Every claim/recommendation stores `source_type`, `source_locator` (slide #, URL, commit hash, transcript ts), `evidence_snippet`, `confidence`.
- `reasoning_traces` per stage: `stage`, `inputs_used` (IDs only), `decision_rule_or_prompt_version`, `output_claim_ids`.
- Serve `GET /recommendation/{id}/trace` for the frontend's "Why this recommendation?" drill-down (≤2 clicks to evidence).
- **Acceptance: 100% of final recommendation bullets have ≥1 evidence locator.**

## 5. Investment Memo Generation

Follow the memo spec exactly (PRD §8):

**Required sections:** Company snapshot · Investment hypotheses · SWOT · Problem & product · Traction & KPIs.
**Optional sections** (include when data exists, else flag): Team & history · Technology & defensibility · Market sizing · Competition · Financials & round structure · Cap table · Due diligence log · Exit perspective.

Hard rules:
- Missing data → explicit flag ("Cap table: not disclosed"), NEVER fabricated. A gap-marked memo scores as more trustworthy.
- No padding — as brief as clarity allows.
- Every claim carries its Trust Score + evidence locator.
- Memo stored as structured JSON in `memos` so the frontend renders sections + flags uniformly.

## 6. Decision Output & SLA Instrumentation

- Final recommendation: $100K yes/no + confidence + key unknowns + Bull/Bear summary.
- `decision_log` with timestamps at every stage (first signal → screen → diligence → decision) to power the live SLA timer. This instrumentation is explicitly rewarded (Investment Utility = 30%).
- Decision outcomes feed Agent B's channel intelligence loop.

## 7. Research Tracks Owned Here

### 7a. Confidence Scoring (PRD §13.1)
- Proxy features: resilience (iteration cadence, recovery after failed launches, consistency), founder-market fit (domain depth, prior same-sector builds).
- Uncertainty-aware output: `score + interval + evidence_coverage` (bootstrap or quantile approximation) → `founder_confidence_intervals`.
- Serve `GET /research/confidence/{founder_id}`.
- **Deliverable:** one-page "Confidence Method Note" (assumptions, features, method, failure modes).

### 7b. Founder Traits & Success (PRD §13.3)
- Public-footprint feature set: posting consistency/depth, technical specificity, engagement quality (not follower count), domain longevity, building-in-public evidence.
- Combine with Wayback narrative signal as the cold-start substitute for GitHub/funding history.
- Document test design + honest limitations (small sample, confounds) — no overclaiming.

## Acceptance Checks

- [ ] 3 independent axis scores with trends for a seeded opportunity; no composite anywhere.
- [ ] Validator catches the seeded contradiction from Agent A's seed data.
- [ ] Full trace: recommendation → claims → evidence locators resolvable in ≤2 clicks worth of API calls.
- [ ] Memo has all 5 required sections + explicit gap flags; zero fabricated data.
- [ ] Bias test passes: strong-execution/zero-network founder outranks weak-execution/strong-network founder on the Founder axis.
- [ ] `decision_log` timestamps power an end-to-end SLA readout.
- [ ] Confidence interval output for at least one founder + method note drafted.
