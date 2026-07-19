/**
 * Local mirror of `shared/schemas/types.ts` (single source of truth).
 * Duplicated here — not imported cross-directory — because Turbopack
 * cannot bundle modules outside the app's project root. Keep in sync
 * per docs/17-PARALLEL-WORKFLOW.md §4 whenever the contract changes.
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
  company_domain?: string | null;
  founder_name: string;
  founder_id: string;
  source: OpportunitySource;
  discovery_channel?: string | null;
  triggering_signal?: string | null;
  /** Connector channels used to discover/enrich this lead (outbound cards). */
  source_channels?: string[];
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
  /** Challenge brief required section (vs optional). */
  required?: boolean;
}

export interface Memo {
  sections: MemoSection[];
}

export interface AdversarialBearPoint {
  point: string;
  severity: "high" | "medium" | "low";
  basis?: string | null;
}

/** Devil's-advocate pass after the Referee memo — the system's call for the
 * human to overrule. bull/bear summaries prefill the decision log. */
export interface AdversarialView {
  bull_summary?: string | null;
  bear_summary?: string | null;
  bear_points: AdversarialBearPoint[];
  kill_criteria: string[];
  recommendation: "yes" | "no" | "needs-more-info";
  confidence: number;
  prompt_version: string;
}

export interface OpportunityDetail {
  id: string;
  company_name: string;
  founder_name: string;
  founder_id: string;
  source: OpportunitySource;
  status?: string | null;
  recommendation?: string | null;
  screen_verdict?: ScreenVerdict | null;
  has_contradiction: boolean;
  axis_scores: AxisScore[];
  claims: ClaimTrust[];
  memo?: Memo | null;
  adversarial?: AdversarialView | null;
  trace_id?: string | null;
  sla?: SlaTimestamps;
}
