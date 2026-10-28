"""Risk and implementation complexity, derived from extracted flags."""

from __future__ import annotations

from app.schemas import Complexity, Extraction, Risk, RiskFactor, StepAssessment

_SEVERITY_ORDER = {"low": 0, "moderate": 1, "high": 2}


def assess_risk(extraction: Extraction, assessments: list[StepAssessment]) -> Risk:
    steps = extraction.steps
    by_id = {a.step_id: a for a in assessments}
    is_ai = lambda s: by_id[s.id].classification == "ai_assisted"  # noqa: E731
    factors: list[RiskFactor] = []

    if any(s.stakes == "consequential" for s in steps):
        factors.append(RiskFactor(
            key="consequential_decision", label="Consequential decisions", severity="high",
            why="The process includes decisions with significant consequences, so final authority stays with a person.",
        ))

    care = sorted({x for s in steps for x in s.sensitivity if x in ("hr", "legal", "health")})
    if care:
        names = " / ".join({"hr": "HR", "legal": "legal", "health": "health"}[c] for c in care)
        factors.append(RiskFactor(
            key="sensitive_matters", label=f"{names} information", severity="high",
            why=f"Involves {names} information. Restrict access, keep an audit trail, and keep judgment human.",
        ))

    pii_steps = [s for s in steps if "pii" in s.sensitivity]
    if pii_steps:
        ai_pii = any(is_ai(s) for s in pii_steps)
        factors.append(RiskFactor(
            key="personal_data", label="Personal data", severity="moderate" if ai_pii else "low",
            why="Personal data would be sent to an AI service; confirm data-handling terms first." if ai_pii
            else "Personal data is only moved by rules-based automation. Keep it within approved systems.",
        ))

    fin_steps = [s for s in steps if "financial" in s.sensitivity]
    if fin_steps:
        interpreted = any(is_ai(s) or s.stakes != "none" for s in fin_steps)
        factors.append(RiskFactor(
            key="financial", label="Financial information", severity="moderate" if interpreted else "low",
            why="Financial figures are interpreted and reported to others; calculations stay deterministic and conclusions are reviewed." if interpreted
            else "Financial figures are only moved or calculated by deterministic steps.",
        ))

    external = [s for s in steps if s.external_facing]
    if external:
        ai_external = any(is_ai(s) for s in external)
        factors.append(RiskFactor(
            key="external_communication", label="External communication",
            severity="moderate" if ai_external else "low",
            why="AI-drafted content leaves the organization, so it is reviewed before sending." if ai_external
            else "Outside recipients only receive fixed, pre-approved templates.",
        ))

    ai_steps = [a for a in assessments if a.classification == "ai_assisted"]
    if ai_steps:
        reviewed = any(a.review_gate for a in ai_steps)
        factors.append(RiskFactor(
            key="ai_accuracy", label="AI output accuracy", severity="moderate" if reviewed else "low",
            why="AI-generated content can be confidently wrong. Outputs others rely on pass a human review gate." if reviewed
            else "AI output is low-stakes and internal; periodic spot-checks are enough.",
        ))

    if _has_fetch_then_process(extraction):
        factors.append(RiskFactor(
            key="data_validation", label="Data validation", severity="low",
            why="Automated data pulls can fail silently. Validation checks run before any calculation.",
        ))

    if not factors:
        return Risk(level="low", factors=[RiskFactor(
            key="none_identified", label="No major risk flags", severity="low",
            why="No sensitive data, external communication, or consequential decisions were identified.",
        )])

    level = max((f.severity for f in factors), key=_SEVERITY_ORDER.__getitem__)
    factors.sort(key=lambda f: -_SEVERITY_ORDER[f.severity])
    return Risk(level=level, factors=factors)


def assess_complexity(extraction: Extraction, assessments: list[StepAssessment]) -> Complexity:
    points = 0
    drivers: list[str] = []

    systems = {name.strip().lower() for s in extraction.steps for name in s.systems if name.strip()}
    if len(systems) >= 6:
        points += 2
        drivers.append(f"{len(systems)} systems to connect")
    elif len(systems) >= 3:
        points += 1
        drivers.append(f"{len(systems)} systems to connect")

    access_points = {"connected": 0, "file_based": 1, "unknown": 1, "manual_only": 2}[extraction.data_access]
    points += access_points
    if access_points:
        drivers.append({
            "file_based": "Data arrives as exported files rather than through APIs",
            "unknown": "It's unclear how data can be accessed programmatically",
            "manual_only": "Some systems have no export or API, so data may need a workaround",
        }[extraction.data_access])

    ai_count = sum(a.classification == "ai_assisted" for a in assessments)
    if ai_count:
        points += 1 if ai_count < 3 else 2
        drivers.append(f"{ai_count} AI-assisted step{'s' if ai_count > 1 else ''} needing prompt design and evaluation")

    level = "low" if points <= 2 else "moderate" if points <= 4 else "high"
    return Complexity(level=level, drivers=drivers or ["Few systems, and the steps are all well defined"])


def _has_fetch_then_process(extraction: Extraction) -> bool:
    seen_fetch = False
    for s in extraction.steps:
        if s.action_type in ("retrieve_data", "move_data"):
            seen_fetch = True
        elif seen_fetch and s.action_type in ("transform_calculate", "compare_analyze"):
            return True
    return False
