"""Automation Potential score.

A transparent weighted sum of seven factors (each 0-1) minus penalties for
risk and implementation complexity. The score measures how much of the
process can be taken off people's plates; it deliberately does NOT reward
using AI. A fully deterministic process can score in the 90s with zero AI.
"""

from __future__ import annotations

from app.schemas import (
    Band,
    Complexity,
    Extraction,
    FactorScore,
    Impact,
    Penalty,
    Risk,
    ScoreResult,
    StepAssessment,
)

WEIGHTS = {
    "frequency": 15,
    "automatable_share": 25,
    "data_handling": 15,
    "structured_data": 10,
    "consistency": 10,
    "time_burden": 10,
    "low_judgment": 15,
}
assert sum(WEIGHTS.values()) == 100

FACTOR_INFO = {
    "frequency": ("Repetition", "How often the process runs. More frequent work pays back automation faster."),
    "automatable_share": ("Automatable steps", "Share of steps that rules can handle, with AI-assisted steps counted at 60% because they still need oversight."),
    "data_handling": ("Manual data handling", "Share of steps that fetch, copy, or reshape data by hand."),
    "structured_data": ("Structured data", "How much of the input is tables, records, or form fields rather than free text."),
    "consistency": ("Process consistency", "Whether the steps are the same every time or vary case by case."),
    "time_burden": ("Time burden", "Total manual hours per year, from step durations and frequency."),
    "low_judgment": ("Low judgment required", "Share of steps that do not depend on human discretion."),
}

FREQUENCY_VALUE = {
    "daily": 1.0, "weekly": 0.8, "biweekly": 0.7, "monthly": 0.5,
    "quarterly": 0.3, "ad_hoc": 0.15, "unknown": 0.5,
}
CONSISTENCY_VALUE = {"standardized": 1.0, "mostly": 0.6, "varies": 0.2}
INPUT_STRUCTURE_VALUE = {"structured": 1.0, "semi_structured": 0.5, "unstructured": 0.0}
AI_STEP_CREDIT = 0.6  # AI-assisted steps still need oversight, so they count partially
DATA_HANDLING_ACTIONS = {"retrieve_data", "move_data", "transform_calculate", "file_management"}

RISK_PENALTY = {"low": 0, "moderate": -5, "high": -15}
COMPLEXITY_PENALTY = {"low": 0, "moderate": -4, "high": -10}
UNKNOWN_VALUE = 0.5  # neutral value when information is missing (always flagged as assumed)


BANDS: list[tuple[int, Band]] = [(75, "high"), (50, "moderate"), (25, "limited"), (0, "keep_human_led")]


def band_for(score: int) -> Band:
    return next(band for floor, band in BANDS if score >= floor)


def compute_score(
    extraction: Extraction,
    assessments: list[StepAssessment],
    impact: Impact,
    risk: Risk,
    complexity: Complexity,
) -> ScoreResult:
    steps = extraction.steps
    n = len(steps)
    by_id = {a.step_id: a for a in assessments}
    count = lambda c: sum(a.classification == c for a in assessments)  # noqa: E731
    n_ta, n_ai = count("traditional_automation"), count("ai_assisted")
    factors: list[FactorScore] = []

    def add(key: str, value: float, explanation: str, assumed: bool = False) -> None:
        value = max(0.0, min(1.0, value))
        factors.append(FactorScore(
            key=key, label=FACTOR_INFO[key][0], weight=WEIGHTS[key], value=round(value, 2),
            points=round(WEIGHTS[key] * value, 1), explanation=explanation, assumed=assumed,
        ))

    freq_unknown = extraction.frequency == "unknown" and impact.runs_per_year is None
    if impact.runs_per_year is not None and extraction.frequency in ("unknown", "ad_hoc"):
        freq_value = _value_from_runs(impact.runs_per_year)
    else:
        freq_value = FREQUENCY_VALUE[extraction.frequency]
    add("frequency", freq_value,
        "Frequency wasn't stated, so it's scored at a neutral value." if freq_unknown
        else f"Runs {_freq_text(extraction, impact)}.",
        assumed=freq_unknown)

    add("automatable_share", (n_ta + AI_STEP_CREDIT * n_ai) / n,
        f"{n_ta} rule-based and {n_ai} AI-assisted out of {n} steps. AI-assisted steps count at "
        f"{int(AI_STEP_CREDIT * 100)}% because they still need oversight.")

    handling = sum(
        s.action_type in DATA_HANDLING_ACTIONS
        or (s.action_type == "compare_analyze" and s.output_nature == "deterministic")
        for s in steps
    )
    add("data_handling", handling / n,
        f"{handling} of {n} steps fetch, copy, or reshape data by hand.")

    structured = sum(INPUT_STRUCTURE_VALUE[s.input_data] for s in steps) / n
    add("structured_data", structured,
        f"About {round(structured * 100)}% of step inputs are structured data.")

    add("consistency", CONSISTENCY_VALUE[extraction.consistency], {
        "standardized": "The steps are the same every time.",
        "mostly": "The steps are mostly the same, with some exceptions.",
        "varies": "Each case is handled differently.",
    }[extraction.consistency])

    if impact.current_minutes_per_run is not None and impact.runs_per_year is not None:
        hours = impact.current_minutes_per_run * impact.runs_per_year / 60
        add("time_burden", _value_from_hours(hours),
            f"About {round(hours)} hours a year of manual effort today.")
    else:
        add("time_burden", UNKNOWN_VALUE,
            "Yearly effort can't be calculated without both duration and frequency, so it's scored neutrally.",
            assumed=True)

    judged = sum(
        s.requires_judgment or s.output_nature == "judgment" or by_id[s.id].classification == "human_review"
        for s in steps
    )
    add("low_judgment", 1 - judged / n,
        f"{judged} of {n} steps need human judgment." if judged else "No step needs human judgment.")

    penalties: list[Penalty] = []
    if RISK_PENALTY[risk.level]:
        penalties.append(Penalty(key="risk", label=f"{risk.level.capitalize()} risk",
                                 points=RISK_PENALTY[risk.level],
                                 explanation="Higher-risk processes need more safeguards, which limits how much can be automated."))
    if COMPLEXITY_PENALTY[complexity.level]:
        penalties.append(Penalty(key="complexity", label=f"{complexity.level.capitalize()} complexity",
                                 points=COMPLEXITY_PENALTY[complexity.level],
                                 explanation="; ".join(complexity.drivers) + "."))

    raw = sum(f.points for f in factors) + sum(p.points for p in penalties)
    score = int(max(0, min(100, round(raw))))
    return ScoreResult(score=score, band=band_for(score), factors=factors, penalties=penalties)


def _value_from_runs(runs: int) -> float:
    if runs >= 250:
        return 1.0
    if runs >= 52:
        return 0.8
    if runs >= 12:
        return 0.5
    return 0.15


def _value_from_hours(hours: float) -> float:
    if hours >= 100:
        return 1.0
    if hours >= 50:
        return 0.8
    if hours >= 20:
        return 0.6
    if hours >= 5:
        return 0.35
    return 0.15


def _freq_text(extraction: Extraction, impact: Impact) -> str:
    if extraction.frequency in ("unknown", "ad_hoc") and impact.runs_per_year:
        return f"about {impact.runs_per_year} times a year"
    return {
        "daily": "daily", "weekly": "weekly", "biweekly": "every two weeks", "monthly": "monthly",
        "quarterly": "quarterly", "ad_hoc": "occasionally, as cases come up",
    }[extraction.frequency]
