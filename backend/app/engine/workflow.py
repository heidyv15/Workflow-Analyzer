"""Current and recommended workflow sequences.

The future workflow is built from the current steps plus nodes the engine
inserts itself: a trigger so nobody has to remember to start the process,
a validation check before calculations, and a human review gate whenever
AI output is about to be used or sent.
"""

from __future__ import annotations

from app.schemas import Classification, Extraction, NodeCategory, StepAssessment, WorkflowNode

CATEGORY: dict[Classification, NodeCategory] = {
    "traditional_automation": "automated",
    "ai_assisted": "ai_assisted",
    "human_review": "human_review",
    "manual": "manual",
}
TRIGGER_LABELS = {"scheduled": "Scheduled trigger", "event": "Event trigger"}
FETCH_ACTIONS = {"retrieve_data", "move_data"}
PROCESS_ACTIONS = {"transform_calculate", "compare_analyze"}


def build_current_workflow(extraction: Extraction) -> list[WorkflowNode]:
    return [
        WorkflowNode(id=f"c-{s.id}", label=s.label, category="manual", source_step_id=s.id)
        for s in extraction.steps
    ]


def build_future_workflow(extraction: Extraction, assessments: list[StepAssessment]) -> list[WorkflowNode]:
    by_id = {a.step_id: a for a in assessments}
    steps = extraction.steps
    nodes: list[WorkflowNode] = []

    if steps[0].action_type != "trigger" and extraction.trigger in TRIGGER_LABELS:
        nodes.append(WorkflowNode(
            id="f-trigger", label=TRIGGER_LABELS[extraction.trigger], category="automated", inserted=True,
            note="Starts the workflow automatically instead of relying on someone to remember.",
        ))

    validation_at = _validation_index(extraction, by_id)
    pending_review = False
    gate_count = 0

    def add_gate() -> None:
        nonlocal gate_count
        gate_count += 1
        nodes.append(WorkflowNode(
            id=f"f-review-{gate_count}", label="Human review", category="human_review", inserted=True,
            note="A person checks AI-generated output before it is used or sent.",
        ))

    for i, step in enumerate(steps):
        a = by_id[step.id]
        if i == validation_at:
            nodes.append(WorkflowNode(
                id="f-validate", label="Data validation", category="automated", inserted=True,
                note="Checks that every expected input arrived and is well formed before anything is calculated.",
            ))
        if step.action_type == "communicate" and pending_review:
            add_gate()
            pending_review = False

        nodes.append(WorkflowNode(
            id=f"f-{step.id}",
            label=step.future_label if a.classification != "human_review" else step.label,
            category=CATEGORY[a.classification],
            source_step_id=step.id,
        ))

        if a.classification == "ai_assisted" and a.review_gate:
            pending_review = True
        elif a.classification == "human_review":
            pending_review = False

    if pending_review:
        add_gate()
    return nodes


def _validation_index(extraction: Extraction, by_id: dict[str, StepAssessment]) -> int | None:
    """Index of the first automated processing step that follows an automated fetch."""
    seen_fetch = False
    for i, s in enumerate(extraction.steps):
        automated = by_id[s.id].classification == "traditional_automation"
        if s.action_type in FETCH_ACTIONS and automated:
            seen_fetch = True
        elif seen_fetch and s.action_type in PROCESS_ACTIONS and automated:
            return i
    return None
