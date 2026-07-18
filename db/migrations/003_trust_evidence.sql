-- 003 — Claims, evidence, validation, contradictions, reasoning traces
-- See docs/01-CONTRACTS.md §1, §2 (EvidenceRef, ClaimTrust shapes).

create table if not exists claims (
  id              uuid primary key default gen_random_uuid(),
  opportunity_id  uuid not null references opportunities(id) on delete cascade,
  text            text not null,
  category        text,                 -- traction | revenue | team | market_size | ...
  slide_locator   text,                 -- e.g. "slide 8" for deck-sourced claims
  source          text,
  source_entity_id text,
  fetched_at      timestamptz,
  run_id          uuid,
  created_at      timestamptz not null default now()
);
create index if not exists idx_claims_opportunity on claims (opportunity_id);

create table if not exists evidence (
  id               uuid primary key default gen_random_uuid(),
  source_type      text not null,        -- deck | web | interview | github | wayback | perplexity
  source_locator   text not null,        -- slide number, URL, commit hash, transcript ts
  evidence_snippet text not null,
  url              text,
  captured_at      timestamptz,
  confidence       numeric not null check (confidence >= 0 and confidence <= 1),
  embedding        vector(1536),         -- OpenAI text-embedding-3-small/large dim
  source           text,
  source_entity_id text,
  fetched_at       timestamptz,
  run_id           uuid,
  created_at       timestamptz not null default now()
);
create index if not exists evidence_embedding_idx on evidence
  using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create table if not exists claim_evidence_links (
  id           uuid primary key default gen_random_uuid(),
  claim_id     uuid not null references claims(id) on delete cascade,
  evidence_id  uuid not null references evidence(id) on delete cascade,
  relation     text not null check (relation in ('supports', 'contradicts')),
  confidence   numeric not null check (confidence >= 0 and confidence <= 1),
  created_at   timestamptz not null default now()
);
create index if not exists idx_cel_claim on claim_evidence_links (claim_id);
create index if not exists idx_cel_evidence on claim_evidence_links (evidence_id);
-- lets seed/ingestion upsert on (claim_id, evidence_id) idempotently
create unique index if not exists uq_cel_claim_evidence on claim_evidence_links (claim_id, evidence_id);

create table if not exists claim_validations (
  id                  uuid primary key default gen_random_uuid(),
  claim_id            uuid not null references claims(id) on delete cascade,
  status              validation_status not null,
  confidence_delta    numeric,
  contradiction_reason text,
  required_followup   text,
  trust_score         numeric check (trust_score >= 0 and trust_score <= 1),
  validated_at        timestamptz not null default now()
);
-- MVP: latest validation per claim (re-running the validator overwrites, not appends).
-- Revisit for multi-run validation history in Wave 3 if time allows.
create unique index if not exists uq_claim_validations_claim on claim_validations (claim_id);

create table if not exists contradiction_events (
  id            uuid primary key default gen_random_uuid(),
  claim_id      uuid not null references claims(id) on delete cascade,
  opportunity_id uuid not null references opportunities(id) on delete cascade,
  description   text not null,
  detected_at   timestamptz not null default now()
);
create index if not exists idx_contradiction_opportunity on contradiction_events (opportunity_id);
create unique index if not exists uq_contradiction_claim on contradiction_events (claim_id);

create table if not exists reasoning_traces (
  id                          uuid primary key default gen_random_uuid(),
  opportunity_id              uuid references opportunities(id) on delete cascade,
  stage                       text not null,   -- screen | analyze | validate | memo | decision | skill:<name>
  inputs_used                 jsonb not null default '[]',   -- array of referenced IDs
  decision_rule_or_prompt_version text,
  output_claim_ids            jsonb not null default '[]',
  created_at                  timestamptz not null default now()
);
create index if not exists idx_traces_opportunity on reasoning_traces (opportunity_id);
