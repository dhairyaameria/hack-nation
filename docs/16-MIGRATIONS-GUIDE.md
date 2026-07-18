# 16 — Migrations Guide (Agent A)

**Owner:** Agent A  
**Purpose:** ordered DDL files, FK dependencies, and apply instructions so schema lands in one pass on Supabase.

Full table list: `01-CONTRACTS.md` §1. Thesis DDL: `12-THESIS-SETTINGS-UI.md` §2.

---

## 1. Prerequisites (Supabase SQL editor)

```sql
-- Run once per project
create extension if not exists vector;
create extension if not exists "uuid-ossp";

-- Optional Bronze/Silver/Gold in Postgres (recommended over Databricks for hackathon)
create schema if not exists bronze;
create schema if not exists silver;
create schema if not exists gold;
```

---

## 2. Migration file order

Apply in numeric order. **Do not reorder** — later files assume earlier tables exist.

| File | Contents | Blocks |
|---|---|---|
| `001_extensions_and_enums.sql` | pgvector, enums (`screen_verdict`, `validation_status`, `axis_name`, `trend`, `opportunity_source`, …) | everything |
| `002_core_entities.sql` | `founders`, `companies`, `founder_company_roles`, `thesis_profiles`, `opportunities` | B, D, E |
| `003_trust_evidence.sql` | `claims`, `evidence`, `claim_evidence_links`, `claim_validations`, `contradiction_events`, `reasoning_traces` | B, C |
| `004_scores_profiles.sql` | `founder_score_history`, `founder_genome_snapshots`, `founder_confidence_intervals`, `opportunity_axis_scores` | C, E |
| `005_sourcing_network.sql` | `watchlist_entries`, `channel_*`, `wayback_*`, `network_*` | B |
| `006_memos_decisions.sql` | `memos`, `decision_log` | C, E |
| `007_agent_skills.sql` | `skill_definitions`, `skill_runs`, `chat_sessions`, `chat_messages` | D |
| `008_optional_federated.sql` | `federated_*`, `provenance_ledger` | optional — skip if behind |

---

## 3. Required columns (every ingested table)

```sql
-- append to Bronze-fed tables
source           text not null,
source_entity_id text,
fetched_at       timestamptz not null default now(),
run_id           uuid
```

---

## 4. Non-negotiable constraints

### Three axes — no composite score

```sql
-- opportunity_axis_scores: one row per (opportunity_id, axis)
-- axis in ('founder', 'market', 'idea_vs_market')
-- NO column named composite_score, total_score, or overall
create unique index opp_axis_unique on opportunity_axis_scores (opportunity_id, axis);
```

### One active thesis

```sql
create unique index one_active_thesis on thesis_profiles (is_active) where is_active = true;
```

### pgvector on evidence / deck chunks

```sql
-- example: 1536-dim for OpenAI embeddings
alter table evidence add column if not exists embedding vector(1536);
create index if not exists evidence_embedding_idx on evidence
  using ivfflat (embedding vector_cosine_ops) with (lists = 100);
```

---

## 5. Index recommendations (demo performance)

```sql
create index idx_opportunities_status on opportunities (status);
create index idx_opportunities_thesis on opportunities (thesis_profile_id);
create index idx_claims_opportunity on claims (opportunity_id);
create index idx_founder_score_history on founder_score_history (founder_id, recorded_at desc);
create index idx_network_edges_from on network_edges (from_node_id);
create index idx_network_edges_to on network_edges (to_node_id);
```

---

## 6. Apply methods

### Option A — Supabase SQL editor (fastest for hackathon)

1. Paste each file in order → Run
2. Verify: `\dt` equivalent in Table Editor shows all tables

### Option B — psql

```bash
export DATABASE_URL="postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres"
for f in db/migrations/*.sql; do psql "$DATABASE_URL" -f "$f"; done
```

### Option C — Supabase CLI

```bash
supabase db push
```

---

## 7. Rollback (dev only)

```bash
make db-reset   # drops public tables + re-applies migrations — see Makefile
```

Never run destructive reset against production demo deploy.

---

## 8. Type generation

After migrations apply:

```bash
# optional: generate TS types from Supabase
npx supabase gen types typescript --project-id YOUR_PROJECT > apps/web/lib/database.types.ts
```

Python types live in `shared/schemas/models.py` (manual mirror until codegen wired).

---

## 9. Verification queries (post-migrate)

```sql
select count(*) from information_schema.tables where table_schema = 'public' and table_type = 'BASE TABLE';
-- expect ≥25 core tables

select * from thesis_profiles where is_active = true;
-- 0 rows until seed; 1 row after seed

select column_name from information_schema.columns
where table_name = 'opportunity_axis_scores' and column_name like '%composite%';
-- must return 0 rows
```

---

## 10. Acceptance

- [ ] All migration files apply without error on fresh Supabase project
- [ ] pgvector extension enabled
- [ ] No composite/opportunity score column anywhere
- [ ] `thesis_profiles` + partial unique index on `is_active`
- [ ] Provenance columns on Bronze-fed tables
- [ ] Agent B can insert into `opportunities` + `claims` after `002` + `003` only
