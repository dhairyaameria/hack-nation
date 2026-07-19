-- 011 - Memory layer: documents, chunks, structured facts, actor aliases
-- Unified "company brain" store shared by REST, MCP tools, and pipelines.
-- Design: resolve meaning at write time (LLM fact extraction on ingest),
-- bi-temporal-lite facts (valid_from/valid_until, invalidate not delete),
-- provenance first-class on every chunk/fact. See docs/18-MEMORY-LAYER.md.
-- Requires: vector extension (enabled in 001), founders/companies (002).

do $$ begin
  create type memory_fact_type as enum ('actor', 'decision', 'commitment', 'claim');
exception when duplicate_object then null; end $$;

create table if not exists documents (
  id                uuid primary key default gen_random_uuid(),
  title             text not null,
  doc_type          text,                 -- deck | memo | note | email | ...
  raw_text          text not null,
  founder_id        uuid references founders(id) on delete set null,
  company_id        uuid references companies(id) on delete set null,
  source_type       text not null,        -- deck | email | note | web | ...
  source_locator    text not null,        -- filename, message id, URL
  source_timestamp  timestamptz,
  run_id            uuid,
  created_at        timestamptz not null default now()
);
create index if not exists idx_documents_founder on documents (founder_id);
create index if not exists idx_documents_company on documents (company_id);

create table if not exists document_chunks (
  id                uuid primary key default gen_random_uuid(),
  document_id       uuid not null references documents(id) on delete cascade,
  chunk_index       int not null,
  content           text not null,
  embedding         vector(1536),         -- OpenAI text-embedding-3-small dim
  founder_id        uuid references founders(id) on delete set null,
  company_id        uuid references companies(id) on delete set null,
  source_type       text not null,
  source_locator    text not null,        -- "<doc locator>#chunk-<n>"
  source_timestamp  timestamptz,
  created_at        timestamptz not null default now()
);
create index if not exists idx_chunks_document on document_chunks (document_id);
create index if not exists idx_chunks_founder on document_chunks (founder_id);
create index if not exists idx_chunks_company on document_chunks (company_id);
create index if not exists document_chunks_embedding_idx on document_chunks
  using ivfflat (embedding vector_cosine_ops) with (lists = 100);
-- lets ingest_document upsert chunks idempotently per document
create unique index if not exists uq_chunks_document_index on document_chunks (document_id, chunk_index);

create table if not exists memory_facts (
  id                uuid primary key default gen_random_uuid(),
  fact_type         memory_fact_type not null,
  subject           text not null,        -- canonical actor/company name the fact is about
  body              text not null,        -- one-sentence plain-language statement
  payload           jsonb not null default '{}',  -- structured detail (amounts, dates, parties)
  founder_id        uuid references founders(id) on delete set null,
  company_id        uuid references companies(id) on delete set null,
  document_id       uuid references documents(id) on delete set null,
  confidence        numeric check (confidence >= 0 and confidence <= 1),
  -- bi-temporal-lite: facts are invalidated (valid_until set), never deleted
  valid_from        timestamptz not null default now(),
  valid_until       timestamptz,
  source_type       text not null,
  source_locator    text not null,
  source_timestamp  timestamptz,
  created_at        timestamptz not null default now()
);
create index if not exists idx_facts_type on memory_facts (fact_type);
create index if not exists idx_facts_subject on memory_facts (subject);
create index if not exists idx_facts_founder on memory_facts (founder_id);
create index if not exists idx_facts_document on memory_facts (document_id);

create table if not exists actor_aliases (
  id           uuid primary key default gen_random_uuid(),
  founder_id   uuid not null references founders(id) on delete cascade,
  alias        text not null,             -- email, handle, or name variant
  alias_type   text not null check (alias_type in ('email', 'handle', 'name')),
  created_at   timestamptz not null default now()
);
create index if not exists idx_aliases_founder on actor_aliases (founder_id);
-- one canonical actor per alias string
create unique index if not exists uq_actor_alias on actor_aliases (alias_type, lower(alias));

-- Vector similarity search entry point. The Supabase REST client cannot
-- order by embedding distance directly, so search_memory() calls this via
-- client.rpc("match_document_chunks", ...). Same pattern Supabase docs use.
create or replace function match_document_chunks(
  query_embedding vector(1536),
  match_count int default 8,
  filter_founder_id uuid default null,
  filter_company_id uuid default null
)
returns table (
  id uuid,
  document_id uuid,
  chunk_index int,
  content text,
  founder_id uuid,
  company_id uuid,
  source_type text,
  source_locator text,
  source_timestamp timestamptz,
  similarity float
)
language sql stable
as $$
  select
    c.id, c.document_id, c.chunk_index, c.content,
    c.founder_id, c.company_id,
    c.source_type, c.source_locator, c.source_timestamp,
    1 - (c.embedding <=> query_embedding) as similarity
  from document_chunks c
  where c.embedding is not null
    and (filter_founder_id is null or c.founder_id = filter_founder_id)
    and (filter_company_id is null or c.company_id = filter_company_id)
  order by c.embedding <=> query_embedding
  limit match_count;
$$;
