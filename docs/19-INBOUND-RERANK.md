# 19 — Inbound Perplexity Rerank

**Owner:** Arman (inbound ranking) · schema review: Khaled  
**Purpose:** Rerank all inbound applications against the active fund thesis using Perplexity, driven by pitch-deck content stored in the DB/Storage.

---

## 1. Triggers (UI-free)

The same function `api.ingestion.inbound_rerank.rerank_inbound(trigger=...)` is called from both paths:

| Trigger | How |
|---|---|
| Manual (future button) | `POST /api/v1/inbound/rerank` with optional `{"trigger":"manual"}` |
| Cron / scheduler | `make inbound-rerank` → `jobs/pipelines/inbound_rerank_cron.py` |

Inspect latest order without re-running:

```bash
curl -s http://localhost:8000/api/v1/inbound/ranked | jq
```

---

## 2. Data flow

1. Load every `opportunities` row where `source = 'inbound'`.
2. For each row, resolve deck text:
   - Prefer download from Supabase Storage via `deck_storage_path` (bucket `decks`).
   - Else use extracted `claims` text already in the DB.
3. Call Perplexity Sonar once with the active thesis + all deck excerpts.
4. Write back per opportunity:
   - `inbound_rank` (1 = best fit)
   - `inbound_rank_rationale`
   - `thesis_fit_score` (0–1)
   - `inbound_ranked_at`, `inbound_rank_run_id`
5. **Does not** write or average the three axis scores (Founder / Market / Idea-vs-Market).

---

## 3. Schema (migration `010`)

Added on `opportunities`:

- `deck_url`, `deck_storage_path`, `deck_filename` — pitch deck locator
- `inbound_rank`, `inbound_rank_rationale`, `inbound_ranked_at`, `inbound_rank_run_id`

Inbound submit (`POST /application/submit`) uploads the PDF to the `decks` bucket and persists those locator columns.

**Ops:** create a public (or signed-URL) Storage bucket named `decks` in Supabase before relying on `deck_url`.

Apply migration:

```bash
psql "$DATABASE_URL" -f db/migrations/010_opportunity_deck_and_inbound_rank.sql
```

---

## 4. Cost / scale improvement (documented debt)

**Current assumption:** inbound volume is small (hackathon / demo). We send the full inbound set in **one** Perplexity call per run. That is intentional and cheap enough for tens of decks; it is **not** production-safe.

Improve later when volume grows:

1. **Delta-only rerank** — skip opportunities whose deck/`updated_at` has not changed since `inbound_ranked_at`.
2. **Batching** — chunk into N opportunities per call with a merge-sort of scores.
3. **Cache deck text** — store a `deck_text_excerpt` column so cron does not re-download + re-parse PDFs every hour.
4. **Cheaper model / offline first pass** — heuristic or embedding similarity pre-filter, Perplexity only for the top band.
5. **Rate-limit + Bronze cache** — persist raw Perplexity responses under Bronze keyed by `run_id` (external API discipline from `00-OVERVIEW.md`).

Do not block the demo on these — revisit after G2/G3.

---

## 5. Env

```
PERPLEXITY_API_KEY=pplx-...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
```

If `PERPLEXITY_API_KEY` is missing, the service still writes a deterministic heuristic ranking so the pipeline shape stays demoable.
