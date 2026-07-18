-- 008 — OPTIONAL federated learning module + provenance ledger.
-- Cut first under time pressure (docs/07-EXECUTION.md §3, docs/17-PARALLEL-WORKFLOW.md §9).
-- Do not apply this migration unless Wave 4 federated module is in scope.

create table if not exists federated_rounds (
  id            uuid primary key default gen_random_uuid(),
  round_number  int not null,
  status        text not null default 'pending',  -- pending | aggregating | complete | rejected
  started_at    timestamptz not null default now(),
  completed_at  timestamptz
);

create table if not exists federated_partner_updates (
  id          uuid primary key default gen_random_uuid(),
  round_id    uuid not null references federated_rounds(id) on delete cascade,
  partner_id  text not null,
  update_payload jsonb not null,   -- model weight deltas only, never raw data
  accepted    boolean,
  rejection_reason text,
  submitted_at timestamptz not null default now()
);

create table if not exists provenance_ledger (
  id          uuid primary key default gen_random_uuid(),
  event_hash  text not null,
  prev_hash   text,
  entity_id   uuid not null,
  entity_type text not null,
  source      text not null,
  recorded_at timestamptz not null default now()
);
create index if not exists idx_provenance_entity on provenance_ledger (entity_id);
