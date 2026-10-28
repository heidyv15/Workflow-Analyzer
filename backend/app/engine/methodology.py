"""The scoring model, described from the same constants the engine runs on.

The Methodology page renders this, so the documentation can't drift from the code.
"""

from __future__ import annotations

from app.engine.classify import RULES
from app.engine.impact import RUNS_PER_YEAR, TIME_REMOVED
from app.engine.scoring import AI_STEP_CREDIT, BANDS, COMPLEXITY_PENALTY, FACTOR_INFO, RISK_PENALTY, WEIGHTS


def describe() -> dict:
    return {
        "rules": [{"id": rid, "description": desc, "outcome": outcome} for rid, (desc, outcome) in RULES.items()],
        "factors": [
            {"key": key, "label": FACTOR_INFO[key][0], "measures": FACTOR_INFO[key][1], "weight": weight}
            for key, weight in WEIGHTS.items()
        ],
        "penalties": {
            "risk": {level: pts for level, pts in RISK_PENALTY.items() if pts},
            "complexity": {level: pts for level, pts in COMPLEXITY_PENALTY.items() if pts},
        },
        "bands": [{"band": band, "min_score": floor} for floor, band in BANDS],
        "ai_step_credit": AI_STEP_CREDIT,
        "time_removed": {key: {"low": low, "high": high} for key, (low, high) in TIME_REMOVED.items()},
        "runs_per_year": RUNS_PER_YEAR,
    }
