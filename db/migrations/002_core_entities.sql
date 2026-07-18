-- 002 — Core entities: founders, companies, roles, thesis_profiles, opportunities
-- See docs/01-CONTRACTS.md §1, docs/11-ENTITY-MODEL.md, docs/12-THESIS-SETTINGS-UI.md §2.

create table if not exists founders (
  id                uuid primary key default gen_random_uuid(),
  display_name      text not null,
  primary_email     text,
  location          text,
  domain_affinity   jsonb not null default '[]',  -- [{ sector, weight, confidence, evidence_source }]
  source            text,
  source_entity_id  text,
  fetched_at        timestamptz,
  run_id            uuid,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create table if not exists companies (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  domain      text,
  sector      text,
  stage       text,
  description text,
  status      company_status not null default 'active',
  source      text,
  source_entity_id text,
  fetched_at  timestamptz,
  run_id      uuid,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists idx_companies_domain on companies (domain);

create table if not exists founder_company_roles (
  id          uuid primary key default gen_random_uuid(),
  founder_id  uuid not null references founders(id) on delete cascade,
  company_id  uuid not null references companies(id) on delete cascade,
  role        text not null,             -- CEO | CTO | cofounder | ...
  start_date  date,
  end_date    date,
  created_at  timestamptz not null default now()
);
create index if not exists idx_roles_founder on founder_company_roles (founder_id);
create index if not exists idx_roles_company on founder_company_roles (company_id);

create table if not exists thesis_profiles (
  id                     uuid primary key default gen_random_uuid(),
  name                   text not null,
  version                int not null default 1,
  is_active              boolean not null default false,
  sectors                text[] not null,
  stage                  thesis_stage not null,
  geography              text not null,
  check_size_usd         numeric not null,
  ownership_target_pct   numeric,
  risk_appetite          risk_appetite not null,
  exclude_sectors        text[] not null default '{}',
  require_signals        text[] not null default '{}',
  watchlist_promotion_threshold numeric not null default 0.65,
  notes                  text,
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now()
);
-- only one active thesis at a time
create unique index if not exists one_active_thesis on thesis_profiles (is_active) where is_active = true;

create table if not exists opportunities (
  id                 uuid primary key default gen_random_uuid(),
  founder_id         uuid not null references founders(id),
  company_id         uuid not null references companies(id),
  thesis_profile_id  uuid references thesis_profiles(id),
  source             opportunity_source not null,
  discovery_channel  text,
  triggering_signal  text,
  screen_verdict     screen_verdict,
  thesis_fit_score   numeric,
  status             text not null default 'discovered',
  has_contradiction  boolean not null default false,
  source_entity_id   text,
  fetched_at         timestamptz,
  run_id             uuid,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);
create index if not exists idx_opportunities_status on opportunities (status);
create index if not exists idx_opportunities_thesis on opportunities (thesis_profile_id);
create index if not exists idx_opportunities_founder on opportunities (founder_id);
