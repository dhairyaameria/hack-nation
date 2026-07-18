-- 007 — Cursor Skills catalog mirror + VC Agent Chat sessions
-- Source of truth remains `.cursor/skills/*/SKILL.md` — see docs/01-CONTRACTS.md §4.

create table if not exists skill_definitions (
  id             uuid primary key default gen_random_uuid(),
  name           text not null unique,       -- matches .cursor/skills/<name>/
  skill_path     text not null,
  input_schema   jsonb,
  tool_bindings  text[] not null default '{}',
  output_contract text,
  created_at     timestamptz not null default now()
);

create table if not exists skill_runs (
  id              uuid primary key default gen_random_uuid(),
  skill_name      text not null,
  input_params    jsonb not null default '{}',
  data_snapshot_refs jsonb not null default '[]',
  output          jsonb,
  citations       jsonb not null default '[]',
  opportunity_id  uuid references opportunities(id),
  created_at      timestamptz not null default now()
);
create index if not exists idx_skill_runs_skill on skill_runs (skill_name);
create index if not exists idx_skill_runs_opportunity on skill_runs (opportunity_id);

create table if not exists chat_sessions (
  id          uuid primary key default gen_random_uuid(),
  title       text,
  created_at  timestamptz not null default now()
);

create table if not exists chat_messages (
  id            uuid primary key default gen_random_uuid(),
  session_id    uuid not null references chat_sessions(id) on delete cascade,
  role          text not null check (role in ('user', 'assistant')),
  content       text not null,
  skill_run_ids uuid[] not null default '{}',
  created_at    timestamptz not null default now()
);
create index if not exists idx_chat_messages_session on chat_messages (session_id);
