# 07 — Execution Plan, Integration & Demo (Team Lead / Integrator)

**Owner:** Team lead (integration, demo, submission artifacts)
**PRD sections covered:** §14, §15, §21–§25.

---

## 1. Milestones & Parallelization

### Milestone 1 — Foundation (all agents unblocked by end)
- **A:** Supabase migrations + seed data (contradictions + bias-test pair included). ← CRITICAL PATH
- **B:** Inbound application flow + deck parser + fast screen.
- **C:** Agent pipeline scaffolding (Analyst/Validator/Referee prompts + structured outputs).
- **D:** Thesis Engine CRUD.
- **E:** App shell, dashboard layout against mocked contracts.

### Milestone 2 — Sourcing Depth (highest judge weight)
- **B:** GitHub + 1 more connector; entity resolution wiring; watchlist state machine; cold-start scoring path.
- **A:** Bronze/Silver/Gold transformations; Gold feature sync.
- **C:** 3-axis scoring against Gold features.
- **D:** Perplexity sweeps → Bronze; NL query endpoint.
- **E:** Opportunity detail + axis cards + trust heatmap.

### Milestone 3 — Trust & Network
- **C:** Claim–evidence linking, validator loop, traceability logging + trace API.
- **B:** Network graph + proximity scoring + GraphQL resolvers; Wayback module.
- **D:** Skill repository core + first 4 skills (`thesis_sourcing_sweep`, `memo_research`, `verify_claim`, `generate_memo`).
- **E:** Founder profile (Genome radar + network badge), evidence drill-down, memo view.

### Milestone 4 — Decision & Copilot
- **C:** Final memo generation + decision log + SLA instrumentation; confidence intervals + method note.
- **B:** Channel intelligence + outcome feedback loop.
- **D:** Copilot router + chat endpoint + re-run/diff.
- **E:** Copilot panel, SLA timer, network explorer, Wayback timeline, thesis switching.
- **Optional (cut first):** federated module (see §3 below).

## 2. Integration Checkpoints

1. **After M1:** one seeded founder visible end-to-end (DB → API → dashboard).
2. **After M2:** inbound deck AND one outbound-discovered founder both reach screening through the SAME code path.
3. **After M3:** seeded contradiction caught by validator and visible in UI; trace drill-down works.
4. **After M4:** full demo dry run against the checklist below, timed.

## 3. Optional Federated Module (only if ahead of schedule)

- 2–3 simulated partner nodes with local synthetic data; FedAvg-style aggregation of model updates only (no raw data leaves partners); versioned global Founder Score component; malformed/outlier update rejection.
- Hash-chained `provenance_ledger` for tamper-evident score/claim lineage.
- Demo line: "Raw founder data never leaves partner institutions; only privacy-preserving updates are aggregated, with verifiable evidence lineage."
- **This is the first thing cut under time pressure.**

## 4. Non-Functional Requirements

- Recommendation within 24h of triggering signal (instrumented).
- Cached opportunity views < ~2s.
- Full provenance/auditability on every score and claim.
- Explicit `unknown`/`not disclosed` everywhere; zero fabricated values.
- Ingestion resilient: retries, idempotency, graceful degradation on rate limits.

## 5. Success Metrics (report in submission)

- % opportunities discovered outbound before inbound contact.
- % memo claims with ≥1 evidence citation (target 100% for required sections).
- % claims through validator before publish (target 100%).
- Contradiction detection yield.
- Median signal-to-decision time (live instrumented).
- Cold-start founder coverage rate.
- Channel quality lift after one feedback cycle.
- Confidence interval calibration (research track).

## 6. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Sparse/noisy founder data | Confidence intervals + explicit `unknown` flags |
| Hallucinated claims | Mandatory validator pass before publish |
| Cold-start ignored | Dedicated path is a first-class milestone (M2) |
| Network-signal bias | Capped/disclosed proximity + bias test in demo |
| External API rate limits | Queue, retry, cache in Bronze |
| Time overrun | Protect sourcing + trust (85% of score); cut federated module first, UI polish second |
| Axis-averaging temptation | Hard rule enforced in schema, API shapes, and UI review |

## 7. Demo Script (target ~5 minutes)

1. Show thesis configuration → switch thesis → top recommendations reorder live.
2. Outbound-discovered founder (before fundraising) with the exact triggering signal.
3. Cold-start founder: Genome radar + public-footprint scoring + Wayback history of a previous dead project + network proximity badge with disclosure.
4. **Bias check:** execution-strong/network-zero founder outranks network-strong/execution-weak founder.
5. Inbound deck → parsed claims → fast screen → 3-axis scores (independent, trended).
6. Validator catches the seeded contradiction live → contradiction alert in UI.
7. Memo with required sections + "not disclosed" flags → claim → evidence drill-down in 2 clicks.
8. Copilot: judge-suggested free-form question → skills route + citations → re-run diff on an earlier question.
9. Close on the SLA timer: "first signal to $100K decision in X — with every claim traceable."

## 8. Demo Acceptance Checklist (full)

- [ ] Outbound-sourced founder shown pre-fundraising, triggering signal displayed.
- [ ] Inbound deck processed via minimal deck + company-name flow.
- [ ] Outbound activation converging into the same screening step as inbound.
- [ ] Three axis scores independent with trends — never averaged.
- [ ] Per-claim Trust Score with exact evidence locators.
- [ ] Seeded contradiction caught live by validator.
- [ ] Reasoning-trace drill-down in ≤2 clicks.
- [ ] Cold-start founder scored with explicit method + confidence.
- [ ] Founder Genome panel with all dimensions + per-dimension evidence.
- [ ] 2nd-degree proximity path shown with disclosure text.
- [ ] Bias check demoed live (execution beats connections).
- [ ] GraphQL network exploration in UI.
- [ ] Wayback timeline with narrative-drift signal.
- [ ] Channel quality ranking + one underexplored suggestion.
- [ ] Memo: 5 required sections + explicit gap flags, zero fabrication.
- [ ] Live SLA timer end-to-end for one opportunity.
- [ ] Compound NL query resolved in one pass with per-clause explanations.
- [ ] Copilot routes a live free-form question with skill names + citations (≥1 Perplexity-backed).
- [ ] Copilot re-run diff demonstrated.
- [ ] Thesis switch changes top recommendation live.
- [ ] (Stretch) Confidence Method Note and/or federated module, limitations stated honestly.

## 9. Submission Artifacts

- Working demo (deployed or local).
- Confidence Method Note (1 page, from Agent C).
- Data-quality thresholds note (from Agent A).
- This docs folder as the architecture/documentation package.
