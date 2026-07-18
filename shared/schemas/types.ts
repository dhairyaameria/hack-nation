/**
 * Single source of truth (mirror) for shared TypeScript shapes.
 * Mirrored from `shared/schemas/models.py`. See `docs/01-CONTRACTS.md` §2.
 * Any change here must be announced per `docs/17-PARALLEL-WORKFLOW.md`.
 */

export type Axis = "founder" | "market" | "idea_vs_market";
export type Trend = "improving" | "stable" | "declining";
export type ValidationStatus =
  | "verified"
  | "contradicted"
  | "weakly_supported"
  | "unknown";
export type ScreenVerdict = "pass" | "reject" | "needs-more-info";
export type OpportunitySource = "inbound" | "outbound";
export type Stage = "pre_seed" | "seed" | "series_a";
export type RiskAppetite = "conservative" | "balanced" | "aggressive";
export type MemoryFactType = "actor" | "decision" | "commitment" | "claim";

export interface EvidenceRef {
  source_type: string;
  source_locator: string;
  evidence_snippet: string;
  confidence: number;
}

export interface AxisScore {
  axis: Axis;
  value: number | string; // market axis may be bullish|neutral|bear
  trend: Trend;
  confidence: number;
  evidence: EvidenceRef[];
}

export interface ClaimTrust {
  claim_id: string;
  text: string;
  trust_score: number;
  validation_status: ValidationStatus;
  evidence: EvidenceRef[];
}

export interface DomainAffinity {
  sector: string;
  weight: number;
  confidence: number;
  evidence_source: string;
}

export interface ThesisProfile {
  id?: string | null;
  name: string;
  version: number;
  is_active: boolean;
  sectors: string[];
  stage: Stage;
  geography: string;
  check_size_usd: number;
  ownership_target_pct?: number | null;
  risk_appetite: RiskAppetite;
  exclude_sectors: string[];
  require_signals: string[];
  watchlist_promotion_threshold: number;
  notes?: string | null;
}

export interface GenomeDimension {
  value: number;
  trend: Trend;
  confidence: number;
  evidence: EvidenceRef[];
}

export interface FounderGenomeSnapshot {
  founder_id: string;
  execution_velocity: GenomeDimension;
  technical_depth: GenomeDimension;
  resilience_proxy: GenomeDimension;
  public_footprint_depth: GenomeDimension;
  network_embeddedness: GenomeDimension; // capped ~10-15% weight in Founder axis
  recorded_at: string;
}

export interface FounderScorePoint {
  recorded_at: string;
  score: number;
}

export interface NetworkProximity {
  proximity_score: number;
  confidence: number;
  disclosure: string; // mandatory plain-language disclosure
}

export interface SlaTimestamps {
  signal_at: string | null;
  screening_at: string | null;
  diligence_at: string | null;
  decision_at: string | null;
}

export interface OpportunitySummary {
  id: string;
  company_name: string;
  founder_name: string;
  founder_id: string;
  source: OpportunitySource;
  discovery_channel?: string | null;
  triggering_signal?: string | null;
  screen_verdict?: ScreenVerdict | null;
  thesis_fit_score?: number | null;
  status: string;
  has_contradiction: boolean;
  axis_scores: AxisScore[];
  sla: SlaTimestamps;
}

export interface MemoSection {
  title: string;
  content?: string | null;
  not_disclosed: boolean;
}

export interface Memo {
  sections: MemoSection[];
}

export interface OpportunityDetail {
  id: string;
  company_name: string;
  founder_name: string;
  founder_id: string;
  source: OpportunitySource;
  screen_verdict?: ScreenVerdict | null;
  has_contradiction: boolean;
  axis_scores: AxisScore[];
  claims: ClaimTrust[];
  memo?: Memo | null;
  trace_id?: string | null;
}

/** Where a chunk/fact came from. Mandatory on every memory row. */
export interface Provenance {
  source_type: string; // deck | memo | note | email | web | ...
  source_locator: string; // filename, message id, URL, "<locator>#chunk-<n>"
  source_timestamp?: string | null;
}

export interface Document {
  id?: string | null;
  title: string;
  doc_type?: string | null; // deck | memo | note | email
  raw_text: string;
  founder_id?: string | null;
  company_id?: string | null;
  provenance: Provenance;
}

export interface DocumentChunk {
  id?: string | null;
  document_id: string;
  chunk_index: number;
  content: string;
  founder_id?: string | null;
  company_id?: string | null;
  provenance: Provenance;
  similarity?: number | null; // populated by search_memory
}

/**
 * Write-time extracted fact. Bi-temporal-lite: invalidated facts keep
 * their row with valid_until set, never deleted.
 */
export interface MemoryFact {
  id?: string | null;
  fact_type: MemoryFactType;
  subject: string; // canonical actor/company name the fact is about
  body: string; // one-sentence plain-language statement
  payload: Record<string, unknown>;
  founder_id?: string | null;
  company_id?: string | null;
  document_id?: string | null;
  confidence?: number | null;
  valid_from?: string | null;
  valid_until?: string | null;
  provenance: Provenance;
}
