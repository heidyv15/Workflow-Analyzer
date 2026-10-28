"""Step classification: a small, ordered decision table.

Rules are checked top to bottom and the first match wins. The order is the
product philosophy expressed as code:

1. Protect consequential human judgment first.
2. Prefer deterministic automation whenever a step can be fully specified.
3. Reach for AI only when a step genuinely involves language or ambiguity.
"""

from __future__ import annotations

from app.schemas import Classification, ExtractedStep, StepAssessment

# Plain-language summary of each rule, in evaluation order (shown in the UI and methodology).
RULES = {
    "R1": ("Consequential decisions stay with a person", "human_review"),
    "R2": ("Judgment that is consequential or involves HR, legal, or health matters stays human", "human_review"),
    "R3": ("Steps that can be fully specified use rule-based automation, even if AI could do them", "traditional_automation"),
    "R4": ("Low-stakes judgment: AI suggests, a person confirms", "ai_assisted"),
    "R5": ("Language or unstructured input: AI drafts or extracts, reviewed when others rely on it", "ai_assisted"),
    "R6": ("Not enough detail to decide: clarify before automating", "manual"),
}

# Actions that handle files or records without needing to understand their contents.
CONTENT_AGNOSTIC_ACTIONS = {"retrieve_data", "file_management"}
HIGH_CARE_SENSITIVITY = {"hr": "HR", "legal": "legal", "health": "health"}

DETERMINISTIC_REASONS = {
    "trigger": "Schedules and event triggers are built into every workflow tool.",
    "retrieve_data": "Fetching files or records from known sources is a connector or API task. It is predictable and repeatable.",
    "move_data": "Copying structured fields between systems is deterministic. An integration does it without re-typing errors.",
    "transform_calculate": "Deterministic data transformation. Formulas or a script give exact, auditable results; no LLM is needed.",
    "compare_analyze": "Comparing against a baseline is a calculation. Thresholds flag changes reliably and the same way every time.",
    "generate_text": "The output follows a fixed template, so a template fill is more reliable than generated text.",
    "classify_route": "Routing follows explicit rules, so conditional logic is more predictable than a model.",
    "communicate": "Sending a predefined message is a standard notification. Nothing needs to be generated.",
    "decide_approve": "The decision follows explicit criteria that can be written as business rules.",
    "file_management": "Creating, naming, and moving files follows fixed rules.",
}

AI_REASONS = {
    "generate_text": "Requires natural-language synthesis. A good fit for an LLM, as long as the output is reviewed.",
    "classify_route": "Inputs are ambiguous, so sorting them benefits from language understanding that fixed rules lack.",
    "compare_analyze": "Explaining what changed and why takes contextual reasoning across the data.",
    "move_data": "Pulling fields out of unstructured input is where AI extraction beats manual re-entry.",
    "transform_calculate": "The input is unstructured, so AI is needed to extract it into a structured form first.",
}
DEFAULT_AI_REASON = "Involves unstructured information that fixed rules cannot handle reliably."


def classify_step(step: ExtractedStep) -> StepAssessment:
    judgment = step.requires_judgment or step.output_nature == "judgment"
    high_care = [HIGH_CARE_SENSITIVITY[s] for s in step.sensitivity if s in HIGH_CARE_SENSITIVITY]

    # R1: consequential decisions stay with a person.
    if step.action_type == "decide_approve" and step.stakes == "consequential":
        return _assess(
            step, "human_review", "R1",
            "Keep the decision with a person; automation can prepare the information",
            "Consequential decision. Accountability has to stay with a person, so the decision itself is not delegated to software.",
        )

    # R2: judgment that is consequential or touches people's HR, legal, or health matters.
    if judgment and (step.stakes == "consequential" or high_care):
        if high_care:
            reason = f"Judgment about {' / '.join(high_care)} matters affects people directly. AI should not make this call."
        else:
            reason = "Consequential judgment. AI can help organize information, but the conclusion stays with a person."
        return _assess(
            step, "human_review", "R2",
            "Keep human judgment; tools can gather and organize the inputs",
            reason,
        )

    # R3: fully specifiable steps get traditional automation, even when AI could do them.
    if (
        not judgment
        and step.output_nature in ("deterministic", "templated")
        and (step.input_data != "unstructured" or step.action_type in CONTENT_AGNOSTIC_ACTIONS)
    ):
        return _assess(
            step, "traditional_automation", "R3",
            "Automate with a rules-based workflow",
            DETERMINISTIC_REASONS[step.action_type],
        )

    # R4: low-stakes judgment. AI proposes, a person confirms.
    if judgment:
        return _assess(
            step, "ai_assisted", "R4",
            "Let AI suggest; a person makes the call",
            "Low-stakes judgment. AI can propose an answer to save time, but a person confirms it.",
            review_gate=True,
        )

    # R5: language or unstructured input is where AI earns its place.
    if step.output_nature == "variable_language" or step.input_data == "unstructured":
        gate = step.external_facing or step.stakes != "none" or bool(step.sensitivity)
        return _assess(
            step, "ai_assisted", "R5",
            "Use AI for a first draft; a person reviews it before use" if gate
            else "Use AI, with periodic spot-checks",
            AI_REASONS.get(step.action_type, DEFAULT_AI_REASON),
            review_gate=gate,
        )

    # R6: defensive fallback. Never guess.
    return _assess(
        step, "manual", "R6",
        "Clarify this step before automating it",
        "There is not enough detail to tell how this step works.",
    )


def _assess(
    step: ExtractedStep,
    classification: Classification,
    rule_id: str,
    recommendation: str,
    reason: str,
    review_gate: bool = False,
) -> StepAssessment:
    return StepAssessment(
        step_id=step.id,
        label=step.label,
        classification=classification,
        recommendation=recommendation,
        reason=reason,
        rule_id=rule_id,
        review_gate=review_gate,
        minutes=step.minutes,
        minutes_source=step.minutes_source,
    )
