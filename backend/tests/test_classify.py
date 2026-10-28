from app.engine.classify import classify_step
from tests.factories import make_step


def test_consequential_decision_stays_human():
    a = classify_step(make_step(action_type="decide_approve", stakes="consequential", output_nature="judgment"))
    assert (a.classification, a.rule_id) == ("human_review", "R1")


def test_rule_based_approval_is_automated():
    # "Approve expenses under $50" is a business rule, not a judgment call.
    a = classify_step(make_step(action_type="decide_approve", stakes="low", output_nature="deterministic"))
    assert a.classification == "traditional_automation"


def test_hr_judgment_stays_human_even_when_low_stakes():
    a = classify_step(make_step(requires_judgment=True, output_nature="judgment", stakes="low", sensitivity=["hr"]))
    assert (a.classification, a.rule_id) == ("human_review", "R2")


def test_deterministic_work_is_never_sent_to_ai():
    for action in ("move_data", "transform_calculate", "file_management", "communicate", "trigger"):
        a = classify_step(make_step(action_type=action, output_nature="deterministic"))
        assert a.classification == "traditional_automation", action


def test_templated_external_email_is_automation_not_ai():
    a = classify_step(make_step(action_type="communicate", output_nature="templated", external_facing=True))
    assert a.classification == "traditional_automation"


def test_fetching_unstructured_files_does_not_need_ai():
    a = classify_step(make_step(action_type="retrieve_data", input_data="unstructured"))
    assert a.classification == "traditional_automation"


def test_entering_data_from_unstructured_input_uses_ai():
    a = classify_step(make_step(action_type="move_data", input_data="unstructured"))
    assert (a.classification, a.rule_id) == ("ai_assisted", "R5")


def test_external_ai_draft_gets_review_gate():
    a = classify_step(make_step(action_type="generate_text", output_nature="variable_language", external_facing=True))
    assert a.classification == "ai_assisted" and a.review_gate


def test_internal_low_stakes_ai_needs_only_spot_checks():
    a = classify_step(make_step(action_type="classify_route", input_data="unstructured", output_nature="variable_language"))
    assert a.classification == "ai_assisted" and not a.review_gate


def test_low_stakes_judgment_is_ai_suggests_human_confirms():
    a = classify_step(make_step(action_type="classify_route", output_nature="judgment", stakes="low"))
    assert (a.classification, a.rule_id, a.review_gate) == ("ai_assisted", "R4", True)
