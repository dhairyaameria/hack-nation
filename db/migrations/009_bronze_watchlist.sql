-- 009 — Bronze raw ingestion + watchlist/opportunity convergence link
-- See docs/03-SOURCING.md §2-3.

-- Physically in `public` (not the `bronze` schema) because Supabase's
-- PostgREST layer only exposes `public`/`graphql_public` by default and
-- we want this reachable from the same supabase-py client as everything
-- else without a project-level API config change. Conceptually this IS
-- the Bronze layer (raw, provenance-tagged, unprocessed).
create table if not exists bronze_raw_events (
  id                uuid primary key default gen_random_uuid(),
  source            text not null,        -- 'github' | 'hackernews' | ...
  source_entity_id  text,                 -- github username, HN query, etc.
  entity_type       text,                 -- 'founder' | 'company' | 'repo' | 'story'
  payload           jsonb not null,
  fetched_at        timestamptz not null default now(),
  run_id            uuid,
  created_at        timestamptz not null default now()
);
create index if not exists idx_bronze_raw_source on bronze_raw_events (source, source_entity_id);

-- Convergence: an activated watchlist entry creates a real opportunity
-- through the same code path as inbound applications (docs/03-SOURCING.md §3).
alter table watchlist_entries add column if not exists opportunity_id uuid references opportunities(id);
alter table watchlist_entries add column if not exists triggering_signal text;
alter table watchlist_entries add column if not exists signals jsonb not null default '[]';
