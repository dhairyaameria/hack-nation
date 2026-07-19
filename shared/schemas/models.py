"""Single source of truth for shared Pydantic shapes.

Mirrored in `shared/schemas/types.ts` for the frontend. Any change here
must be announced to the whole team per `docs/17-PARALLEL-WORKFLOW.md`.
See `docs/01-CONTRACTS.md` §2 for the canonical definitions.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Axis = Literal["founder", "market", "idea_vs_market"]
Trend = Literal["improving", "stable", "declining"]
ValidationStatus = Literal["verified", "contradicted", "weakly_supported", "unknown"]
ScreenVerdict = Literal["pass", "reject", "needs-more-info"]
OpportunitySource = Literal["inbound", "outbound"]
Stage = Literal["pre_seed", "seed", "series_a"]
RiskAppetite = Literal["conservative", "balanced", "aggressive"]
MemoryFactType = Literal["actor", "decision", "commitment", "claim"]


class EvidenceRef(BaseModel):
    source_type: str  # deck | web | interview | github | wayback | perplexity | ...
    source_locator: str  # slide number, URL, commit hash, transcript ts
    evidence_snippet: str
    confidence: float = Field(ge=0, le=1)


class AxisScore(BaseModel):
    axis: Axis
    value: float | str  # market axis may be bullish|neutral|bear
    trend: Trend
    confidence: float = Field(ge=0, le=1)
    evidence: list[EvidenceRef] = Field(default_factory=list)


class ClaimTrust(BaseModel):
    claim_id: str
    text: str
    trust_score: float = Field(ge=0, le=1)
    validation_status: ValidationStatus
    evidence: list[EvidenceRef] = Field(default_factory=list)


class DomainAffinity(BaseModel):
    sector: str
    weight: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence_source: str  # wayback | github | role_history | deck


class ThesisProfile(BaseModel):
    id: str | None = None
    name: str
    version: int = 1
    is_active: bool = False
    sectors: list[str]
    stage: Stage
    geography: str
    check_size_usd: float
    ownership_target_pct: float | None = None
    risk_appetite: RiskAppetite
    exclude_sectors: list[str] = Field(default_factory=list)
    require_signals: list[str] = Field(default_factory=list)
    watchlist_promotion_threshold: float = 0.65
    notes: str | None = None


class GenomeDimension(BaseModel):
    value: float = Field(ge=0, le=1)
    trend: Trend
    confidence: float = Field(ge=0, le=1)
    evidence: list[EvidenceRef] = Field(default_factory=list)


class FounderGenomeSnapshot(BaseModel):
    founder_id: str
    execution_velocity: GenomeDimension
    technical_depth: GenomeDimension
    resilience_proxy: GenomeDimension
    public_footprint_depth: GenomeDimension
    network_embeddedness: GenomeDimension  # capped ~10-15% weight in Founder axis
    recorded_at: str


class FounderScorePoint(BaseModel):
    recorded_at: str
    score: float = Field(ge=0, le=1)


class NetworkProximity(BaseModel):
    proximity_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    disclosure: str  # mandatory plain-language disclosure


class SlaTimestamps(BaseModel):
    signal_at: str | None = None
    screening_at: str | None = None
    diligence_at: str | None = None
    decision_at: str | None = None


class OpportunitySummary(BaseModel):
    """Pipeline dashboard card shape."""

    id: str
    company_name: str
    founder_name: str
    founder_id: str
    source: OpportunitySource
    discovery_channel: str | None = None
    triggering_signal: str | None = None
    screen_verdict: ScreenVerdict | None = None
    thesis_fit_score: float | None = None
    status: str
    has_contradiction: bool = False
    axis_scores: list[AxisScore] = Field(default_factory=list)
    sla: SlaTimestamps = Field(default_factory=SlaTimestamps)


class MemoSection(BaseModel):
    title: str
    content: str | None = None
    not_disclosed: bool = False


class Memo(BaseModel):
    sections: list[MemoSection]


class OpportunityDetail(BaseModel):
    id: str
    company_name: str
    founder_name: str
    founder_id: str
    source: OpportunitySource
    screen_verdict: ScreenVerdict | None = None
    has_contradiction: bool = False
    axis_scores: list[AxisScore] = Field(default_factory=list)
    claims: list[ClaimTrust] = Field(default_factory=list)
    memo: Memo | None = None
    trace_id: str | None = None


class Provenance(BaseModel):
    """Where a chunk/fact came from. Mandatory on every memory row."""

    source_type: str  # deck | memo | note | email | web | ...
    source_locator: str  # filename, message id, URL, "<locator>#chunk-<n>"
    source_timestamp: str | None = None


class Document(BaseModel):
    id: str | None = None
    title: str
    doc_type: str | None = None  # deck | memo | note | email
    raw_text: str
    founder_id: str | None = None
    company_id: str | None = None
    provenance: Provenance


class DocumentChunk(BaseModel):
    id: str | None = None
    document_id: str
    chunk_index: int
    content: str
    founder_id: str | None = None
    company_id: str | None = None
    provenance: Provenance
    similarity: float | None = None  # populated by search_memory


class MemoryFact(BaseModel):
    """Write-time extracted fact. Bi-temporal-lite: invalidated facts keep
    their row with valid_until set, never deleted."""

    id: str | None = None
    fact_type: MemoryFactType
    subject: str  # canonical actor/company name the fact is about
    body: str  # one-sentence plain-language statement
    payload: dict = Field(default_factory=dict)
    founder_id: str | None = None
    company_id: str | None = None
    document_id: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    valid_from: str | None = None
    valid_until: str | None = None
    provenance: Provenance
