-- 010 — Pitch deck locators + inbound Perplexity rerank columns
-- Additive only. Numbered 010 so it does not collide with unmerged
-- `009_memory_layer.sql` on team-k/memory-mcp-scaffold.
-- See docs/19-INBOUND-RERANK.md.

alter table opportunities
  add column if not exists deck_url text,
  add column if not exists deck_storage_path text,
  add column if not exists deck_filename text,
  add column if not exists inbound_rank int,
  add column if not exists inbound_rank_rationale text,
  add column if not exists inbound_ranked_at timestamptz,
  add column if not exists inbound_rank_run_id uuid;

-- Fast path for "show me inbound ordered by latest Perplexity rank"
create index if not exists idx_opportunities_inbound_rank
  on opportunities (inbound_rank)
  where source = 'inbound' and inbound_rank is not null;

comment on column opportunities.deck_url is
  'Public or signed URL for the pitch deck (Supabase Storage or external).';
comment on column opportunities.deck_storage_path is
  'Object path inside the decks bucket, e.g. {opportunity_id}/deck.pdf';
comment on column opportunities.inbound_rank is
  '1-based rank among inbound opportunities from the latest Perplexity rerank run';
