"""Time-savings estimates.

Estimates are directional ranges, never point values. Every figure records
whether it came from the user or was inferred, and annual totals are omitted
entirely when the frequency is unknown.
"""

from __future__ import annotations

from app.schemas import Extraction, Impact, MissingInfo, Range, StepAssessment

RUNS_PER_YEAR = {"daily": 250, "weekly": 52, "biweekly": 26, "monthly": 12, "quarterly": 4}

# Share of a step's time removed after automation, as a (low, high) range.
TIME_REMOVED = {
    "traditional_automation": (0.85, 1.0),
    "ai_assisted_reviewed": (0.40, 0.70),  # review time is kept
    "ai_assisted": (0.60, 0.85),
    "human_review": (0.0, 0.15),           # tools can prepare inputs; the decision takes as long as it takes
    "manual": (0.0, 0.0),
}


def reconcile_minutes(extraction: Extraction) -> Extraction:
    """Scale inferred step durations so they add up to a user-stated total."""
    if extraction.total_minutes_source != "stated" or extraction.total_minutes is None:
        return extraction
    steps = extraction.steps
    stated = sum(s.minutes or 0 for s in steps if s.minutes_source == "stated")
    flexible = [s for s in steps if s.minutes_source != "stated"]
    remaining = max(extraction.total_minutes - stated, 0)
    if not flexible:
        return extraction
    inferred_sum = sum(s.minutes or 0 for s in flexible)
    new_steps = []
    for s in steps:
        if s.minutes_source == "stated":
            new_steps.append(s)
            continue
        share = (s.minutes or 0) / inferred_sum if inferred_sum else 1 / len(flexible)
        new_steps.append(s.model_copy(update={"minutes": round(remaining * share, 1), "minutes_source": "inferred"}))
    return extraction.model_copy(update={"steps": new_steps})


def runs_per_year(extraction: Extraction, override: int | None = None) -> int | None:
    if override is not None:
        return override
    return RUNS_PER_YEAR.get(extraction.frequency)


def compute_impact(
    extraction: Extraction,
    assessments: list[StepAssessment],
    runs_override: int | None = None,
) -> Impact:
    basis: list[str] = []
    missing: list[MissingInfo] = []
    runs = runs_per_year(extraction, runs_override)

    if any(a.minutes is None for a in assessments):
        missing.append(MissingInfo(field="duration", question="Roughly how long does each step take?"))
        return Impact(
            current_minutes_per_run=None,
            future_minutes_per_run=None,
            saved_minutes_per_run=None,
            runs_per_year=runs,
            saved_hours_per_year=None,
            confidence="low",
            basis=["Step durations were not provided, so time savings can't be estimated yet."],
            missing=missing,
        )

    current = sum(a.minutes for a in assessments)
    saved_low = saved_high = 0.0
    for a in assessments:
        key = a.classification
        if key == "ai_assisted" and a.review_gate:
            key = "ai_assisted_reviewed"
        low, high = TIME_REMOVED[key]
        saved_low += a.minutes * low
        saved_high += a.minutes * high

    saved = Range(low=round(saved_low), high=round(saved_high))
    future = Range(low=round(current - saved_high), high=round(current - saved_low))

    if extraction.total_minutes_source == "stated":
        basis.append(f"Total time per run comes from your description ({_fmt_minutes(extraction.total_minutes)}).")
    elif all(a.minutes_source == "stated" for a in assessments):
        basis.append("Step durations come from your description.")
    else:
        basis.append("Some or all step durations are estimates based on typical effort. Edit them for a sharper figure.")

    if runs is not None:
        source = "you entered" if runs_override is not None else extraction.frequency_source
        basis.append(f"Runs about {runs} times a year ({source}).")
        hours = Range(low=_round_hours(saved.low * runs / 60), high=_round_hours(saved.high * runs / 60))
    else:
        hours = None
        missing.append(MissingInfo(
            field="frequency",
            question="How often does this process run? Annual savings need a frequency.",
        ))

    basis.append(
        "Ranges reflect typical time removed: rule-based steps 85–100%, AI-assisted steps "
        "40–85% (review time kept), human decisions 0–15%."
    )

    return Impact(
        current_minutes_per_run=round(current),
        future_minutes_per_run=future,
        saved_minutes_per_run=saved,
        runs_per_year=runs,
        saved_hours_per_year=hours,
        confidence=_confidence(extraction, assessments, runs, runs_override),
        basis=basis,
        missing=missing,
    )


def _confidence(extraction, assessments, runs, runs_override) -> str:
    total = sum(a.minutes for a in assessments) or 1
    stated_share = sum(a.minutes for a in assessments if a.minutes_source == "stated") / total
    if extraction.total_minutes_source == "stated":
        stated_share = max(stated_share, 0.7)
    freq_stated = runs_override is not None or extraction.frequency_source == "stated"

    if runs is None:
        return "low"
    if stated_share >= 0.7 and freq_stated:
        return "high"
    if stated_share >= 0.3 or freq_stated:
        return "medium"
    return "low"


def _round_hours(h: float) -> float:
    return round(h) if h >= 10 else round(h, 1)


def _fmt_minutes(m: float) -> str:
    return f"{m:g} min"
