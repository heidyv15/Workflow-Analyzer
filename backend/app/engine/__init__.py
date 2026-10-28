"""Deterministic analysis engine.

`analyze()` turns a validated `Extraction` into a full `Analysis`. Nothing in
this package calls an LLM, so every number it produces can be reproduced,
tested, and explained.
"""

from __future__ import annotations

from app.engine.architecture import build_architecture
from app.engine.classify import classify_step
from app.engine.impact import compute_impact, reconcile_minutes
from app.engine.risk import assess_complexity, assess_risk
from app.engine.scoring import compute_score
from app.engine.workflow import build_current_workflow, build_future_workflow
from app.schemas import (
    Analysis,
    AnalysisMeta,
    Assumption,
    Extraction,
    MissingInfo,
    Overrides,
    StepAssessment,
)

ENGINE_VERSION = "1.0.0"


class InsufficientDetail(Exception):
    """The description can't be analyzed responsibly; ask the user instead of guessing."""

    def __init__(self, questions: list[MissingInfo]):
        super().__init__("insufficient detail to analyze this process")
        self.questions = questions


def analyze(extraction: Extraction, overrides: Overrides | None = None) -> Analysis:
    if not extraction.is_analyzable:
        raise InsufficientDetail(extraction.missing_information or [
            MissingInfo(field="steps", question="What are the main steps, from what starts the process to what it produces?"),
        ])

    overrides = overrides or Overrides()
    ex = reconcile_minutes(_apply_overrides(extraction, overrides))

    assessments = [classify_step(s) for s in ex.steps]
    impact = compute_impact(ex, assessments, runs_override=overrides.runs_per_year)
    risk = assess_risk(ex, assessments)
    complexity = assess_complexity(ex, assessments)
    score = compute_score(ex, assessments, impact, risk, complexity)

    return Analysis(
        process_name=ex.process_name,
        summary=_summary(assessments, score.band),
        score=score,
        step_analysis=assessments,
        current_workflow=build_current_workflow(ex),
        future_workflow=build_future_workflow(ex, assessments),
        impact=impact,
        risk=risk,
        complexity=complexity,
        architecture=build_architecture(ex, assessments),
        ai_used_for=[a.label for a in assessments if a.classification == "ai_assisted"],
        ai_not_needed=[a.label for a in assessments if a.classification == "traditional_automation"],
        assumptions=_assumptions(ex, overrides),
        missing_information=_merge_missing(ex.missing_information, impact.missing),
        meta=AnalysisMeta(engine_version=ENGINE_VERSION),
    )


def _apply_overrides(extraction: Extraction, overrides: Overrides) -> Extraction:
    update: dict = {}
    if overrides.frequency is not None:
        update["frequency"] = overrides.frequency
        update["frequency_source"] = "stated" if overrides.frequency != "unknown" else "unknown"
    if overrides.step_minutes:
        update["steps"] = [
            s.model_copy(update={"minutes": overrides.step_minutes[s.id], "minutes_source": "stated"})
            if s.id in overrides.step_minutes else s
            for s in extraction.steps
        ]
        # Per-step edits take precedence over a stated total.
        update["total_minutes"] = None
        update["total_minutes_source"] = "unknown"
    return extraction.model_copy(update=update) if update else extraction


def _assumptions(ex: Extraction, overrides: Overrides) -> list[Assumption]:
    out: list[Assumption] = []
    if overrides.runs_per_year is None:
        if ex.frequency_source == "unknown":
            out.append(Assumption(field="frequency", detail="Frequency wasn't stated. It was scored neutrally and annual savings are left out."))
        elif ex.frequency_source == "inferred":
            out.append(Assumption(field="frequency", detail=f"Frequency was inferred as '{ex.frequency.replace('_', ' ')}' from your wording."))
    inferred = [s.label for s in ex.steps if s.minutes_source == "inferred"]
    if inferred and ex.total_minutes_source == "stated":
        out.append(Assumption(field="duration", detail="Your stated total time was split across steps using typical effort for each one."))
    elif inferred:
        out.append(Assumption(field="duration", detail=f"Durations for {len(inferred)} of {len(ex.steps)} steps are estimates, not stated values."))
    if ex.data_access == "unknown":
        out.append(Assumption(field="data_access", detail="It's unclear whether the systems involved have APIs or exports; integration effort may vary."))
    return out


def _merge_missing(*groups: list[MissingInfo]) -> list[MissingInfo]:
    seen: set[str] = set()
    out: list[MissingInfo] = []
    for group in groups:
        for m in group:
            if m.field not in seen:
                seen.add(m.field)
                out.append(m)
    return out


def _summary(assessments: list[StepAssessment], band: str) -> str:
    # Placeholder narrative; an LLM-written summary based on these results comes in a later step.
    n = len(assessments)
    ta = sum(a.classification == "traditional_automation" for a in assessments)
    ai = sum(a.classification == "ai_assisted" for a in assessments)
    hr = sum(a.classification == "human_review" for a in assessments)
    parts = [f"{ta} of {n} steps {'is' if ta == 1 else 'are'} rule-based and suit{'s' if ta == 1 else ''} traditional automation"]
    parts.append(f"{ai} benefit{'s' if ai == 1 else ''} from AI assistance" if ai else "none need AI")
    if hr:
        parts.append(f"{hr} should stay with a person")
    lead = {
        "high": "Strong automation candidate.",
        "moderate": "Worthwhile, selective automation candidate.",
        "limited": "Limited automation opportunity.",
        "keep_human_led": "Keep this process human-led.",
    }[band]
    return f"{lead} {', '.join(parts[:-1])}, and {parts[-1]}." if len(parts) > 1 else f"{lead} {parts[0]}."
