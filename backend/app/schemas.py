"""Data contracts for the analyzer.

There are two contracts, and they are deliberately separate:

* `Extraction` is the only thing the LLM produces. It describes the process as
  facts chosen from closed vocabularies. It contains no scores and no verdicts.
* `Analysis` is what the API returns. Every classification, score, and
  estimate in it is computed by the deterministic engine in `app.engine`.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# --------------------------------------------------------------------------
# Vocabularies
# --------------------------------------------------------------------------

ActionType = Literal[
    "trigger",              # something that starts the process
    "retrieve_data",        # download, export, or fetch from a system
    "move_data",            # copy or re-enter data between systems
    "transform_calculate",  # combine, clean, or calculate
    "compare_analyze",      # compare against a baseline or examine
    "generate_text",        # write a summary, message, or document
    "classify_route",       # sort, tag, or route items
    "communicate",          # send a message or report
    "decide_approve",       # make or approve a decision
    "file_management",      # create, rename, or organize files and folders
]
InputData = Literal["structured", "semi_structured", "unstructured"]
OutputNature = Literal["deterministic", "templated", "variable_language", "judgment"]
Stakes = Literal["none", "low", "consequential"]
Sensitivity = Literal["pii", "financial", "hr", "legal", "health"]
ValueSource = Literal["stated", "inferred", "unknown"]
Trigger = Literal["scheduled", "event", "ad_hoc", "unknown"]
Frequency = Literal["daily", "weekly", "biweekly", "monthly", "quarterly", "ad_hoc", "unknown"]
Consistency = Literal["standardized", "mostly", "varies"]
DataAccess = Literal["connected", "file_based", "manual_only", "unknown"]

Classification = Literal["traditional_automation", "ai_assisted", "human_review", "manual"]
NodeCategory = Literal["automated", "ai_assisted", "human_review", "manual"]
Band = Literal["high", "moderate", "limited", "keep_human_led"]
Level3 = Literal["low", "moderate", "high"]
Confidence = Literal["high", "medium", "low"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------
# Extraction: produced by the LLM, validated before the engine sees it
# --------------------------------------------------------------------------


class ExtractedStep(_Strict):
    id: str = Field(pattern=r"^s\d{1,2}$")
    label: str = Field(min_length=2, max_length=80)
    future_label: str = Field(min_length=2, max_length=80)
    action_type: ActionType
    input_data: InputData
    output_nature: OutputNature
    requires_judgment: bool
    stakes: Stakes
    external_facing: bool
    sensitivity: list[Sensitivity] = Field(default_factory=list)
    minutes: float | None = Field(default=None, ge=0, le=480)
    minutes_source: ValueSource = "unknown"
    systems: list[str] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def _normalize_minutes_source(self) -> ExtractedStep:
        # Benign inconsistencies are corrected rather than rejected.
        if self.minutes is None:
            self.minutes_source = "unknown"
        elif self.minutes_source == "unknown":
            self.minutes_source = "inferred"
        return self


class MissingInfo(_Strict):
    field: Literal["frequency", "duration", "steps", "systems", "volume", "other"]
    question: str = Field(min_length=5, max_length=200)


class Extraction(_Strict):
    is_analyzable: bool
    process_name: str = Field(min_length=2, max_length=60)
    trigger: Trigger
    frequency: Frequency
    frequency_source: ValueSource
    consistency: Consistency
    data_access: DataAccess
    total_minutes: float | None = Field(default=None, ge=0, le=2400)
    total_minutes_source: ValueSource = "unknown"
    steps: list[ExtractedStep] = Field(default_factory=list, max_length=12)
    missing_information: list[MissingInfo] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def _check_consistency(self) -> Extraction:
        if self.is_analyzable and len(self.steps) < 2:
            raise ValueError("an analyzable process needs at least two steps")
        ids = [s.id for s in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("step ids must be unique")
        if self.frequency == "unknown":
            self.frequency_source = "unknown"
        if self.total_minutes is None:
            self.total_minutes_source = "unknown"
        elif self.total_minutes_source == "unknown":
            self.total_minutes_source = "inferred"
        return self


class Overrides(_Strict):
    """User-edited assumptions. Applying them never requires another LLM call."""

    frequency: Frequency | None = None
    runs_per_year: int | None = Field(default=None, ge=1, le=100_000)
    step_minutes: dict[str, Annotated[float, Field(ge=0, le=480)]] = Field(default_factory=dict)


# --------------------------------------------------------------------------
# Analysis: produced by the engine
# --------------------------------------------------------------------------


class StepAssessment(_Strict):
    step_id: str
    label: str
    classification: Classification
    recommendation: str
    reason: str
    rule_id: str
    review_gate: bool
    minutes: float | None
    minutes_source: ValueSource


class WorkflowNode(_Strict):
    id: str
    label: str
    category: NodeCategory
    source_step_id: str | None = None
    inserted: bool = False
    note: str | None = None


class FactorScore(_Strict):
    key: str
    label: str
    weight: int
    value: float = Field(ge=0, le=1)
    points: float
    explanation: str
    assumed: bool = False


class Penalty(_Strict):
    key: str
    label: str
    points: float = Field(le=0)
    explanation: str


class ScoreResult(_Strict):
    score: int = Field(ge=0, le=100)
    band: Band
    factors: list[FactorScore]
    penalties: list[Penalty]


class Range(_Strict):
    low: float
    high: float

    @model_validator(mode="after")
    def _ordered(self) -> Range:
        if self.low > self.high:
            raise ValueError("range low must not exceed high")
        return self


class Impact(_Strict):
    current_minutes_per_run: float | None
    future_minutes_per_run: Range | None
    saved_minutes_per_run: Range | None
    runs_per_year: int | None
    saved_hours_per_year: Range | None
    confidence: Confidence
    basis: list[str]
    missing: list[MissingInfo]


class RiskFactor(_Strict):
    key: str
    label: str
    severity: Level3
    why: str


class Risk(_Strict):
    level: Level3
    factors: list[RiskFactor]


class Complexity(_Strict):
    level: Level3
    drivers: list[str]


class ArchNode(_Strict):
    stage: str
    tool: str
    why: str
    kind: Literal["trigger", "integration", "processing", "ai", "human", "delivery"]


class Assumption(_Strict):
    field: str
    detail: str


class AnalysisMeta(_Strict):
    engine_version: str
    summary_source: Literal["template", "model"] = "template"


class Analysis(_Strict):
    process_name: str
    summary: str
    score: ScoreResult
    step_analysis: list[StepAssessment]
    current_workflow: list[WorkflowNode]
    future_workflow: list[WorkflowNode]
    impact: Impact
    risk: Risk
    complexity: Complexity
    architecture: list[ArchNode]
    ai_used_for: list[str]
    ai_not_needed: list[str]
    assumptions: list[Assumption]
    missing_information: list[MissingInfo]
    meta: AnalysisMeta
