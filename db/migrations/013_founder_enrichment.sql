-- 013 — Founder profile enrichment (public web research via Perplexity/Tavily)
-- Mirrors companies.enrichment from 011_deck_assets.sql.

alter table founders
  add column if not exists enrichment jsonb not null default '{}'::jsonb,
  add column if not exists enrichment_at timestamptz;

comment on column founders.enrichment is
  'Public web research brief (Perplexity/Tavily) with citations — not a licensed data feed.';
