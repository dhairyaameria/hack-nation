-- 011 — Pitch deck assets + company enrichment for inbound cards/profiles

alter table opportunities
  add column if not exists deck_filename text,
  add column if not exists deck_storage_path text;

alter table companies
  add column if not exists enrichment jsonb not null default '{}'::jsonb,
  add column if not exists enrichment_at timestamptz;

comment on column opportunities.deck_storage_path is
  'Relative path under API deck store or Supabase Storage object key';
comment on column companies.enrichment is
  'Perplexity/Tavily company profile payload with citations';
