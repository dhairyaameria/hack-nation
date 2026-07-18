-- 001 — Extensions & enums
-- See docs/16-MIGRATIONS-GUIDE.md. Run once per Supabase project.

create extension if not exists vector;
create extension if not exists "uuid-ossp";
create extension if not exists pgcrypto; -- gen_random_uuid()

do $$ begin
  create type opportunity_source as enum ('inbound', 'outbound');
exception when duplicate_object then null; end $$;

do $$ begin
  create type screen_verdict as enum ('pass', 'reject', 'needs-more-info');
exception when duplicate_object then null; end $$;

do $$ begin
  create type axis_name as enum ('founder', 'market', 'idea_vs_market');
exception when duplicate_object then null; end $$;

do $$ begin
  create type trend as enum ('improving', 'stable', 'declining');
exception when duplicate_object then null; end $$;

do $$ begin
  create type validation_status as enum ('verified', 'contradicted', 'weakly_supported', 'unknown');
exception when duplicate_object then null; end $$;

do $$ begin
  create type thesis_stage as enum ('pre_seed', 'seed', 'series_a');
exception when duplicate_object then null; end $$;

do $$ begin
  create type risk_appetite as enum ('conservative', 'balanced', 'aggressive');
exception when duplicate_object then null; end $$;

do $$ begin
  create type company_status as enum ('active', 'dead', 'acquired');
exception when duplicate_object then null; end $$;

do $$ begin
  create type watchlist_stage as enum (
    'discovered', 'scored', 'activation-candidate', 'outreach-sent', 'applied', 'screening'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type network_node_type as enum ('Founder', 'VC', 'Accelerator', 'Institution', 'Company');
exception when duplicate_object then null; end $$;

do $$ begin
  create type network_edge_type as enum (
    'FOLLOWS', 'CO_CONTRIBUTED', 'CO_AUTHORED', 'CO_PARTICIPATED', 'ALUMNI_OF', 'MENTIONED_BY'
  );
exception when duplicate_object then null; end $$;

-- Optional Bronze/Silver/Gold in Postgres (recommended over Databricks for hackathon)
create schema if not exists bronze;
create schema if not exists silver;
create schema if not exists gold;
