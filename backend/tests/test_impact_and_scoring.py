import pytest
from pydantic import ValidationError

from app.engine import InsufficientDetail, analyze
from app.examples import load_extraction
from app.schemas import Extraction, Overrides
from tests.factories import make_extraction, make_step


def ai_heavy_and_deterministic_twins():
    """Two otherwise-identical processes: one deterministic, one where the work is AI-assisted."""
    det = make_extraction([make_step("s1"), make_step("s2"), make_step("s3")])
    ai = make_extraction([
        make_step("s1"),
        make_step("s2", action_type="generate_text", output_nature="variable_language"),
        make_step("s3", action_type="generate_text", output_nature="variable_language"),
    ])
    return det, ai


def test_score_does_not_reward_using_ai():
    det, ai = ai_heavy_and_deterministic_twins()
    assert analyze(det).score.score > analyze(ai).score.score


def test_breakdown_adds_up_to_score():
    for example_id in ("weekly_sales_report", "intake_form", "employee_review"):
        s = analyze(load_extraction(example_id)).score
        raw = sum(f.points for f in s.factors) + sum(p.points for p in s.penalties)
        assert abs(max(0, min(100, raw)) - s.score) <= 0.5


def test_stated_total_is_split_across_steps():
    ex = make_extraction(
        [make_step("s1", minutes=10, minutes_source="inferred"), make_step("s2", minutes=30, minutes_source="inferred")],
        total_minutes=60, total_minutes_source="stated",
    )
    analysis = analyze(ex)
    assert analysis.impact.current_minutes_per_run == 60
    assert [a.minutes for a in analysis.step_analysis] == [15, 45]


def test_missing_duration_means_no_time_estimate():
    ex = make_extraction([make_step("s1", minutes=None), make_step("s2")])
    impact = analyze(ex).impact
    assert impact.saved_minutes_per_run is None
    assert any(m.field == "duration" for m in impact.missing)


def test_overrides_recompute_without_new_extraction():
    ex = load_extraction("intake_form")
    before = analyze(ex)
    after = analyze(ex, Overrides(runs_per_year=1040, step_minutes={"s1": 6}))
    assert before.impact.saved_hours_per_year is None
    assert after.impact.saved_hours_per_year is not None
    assert after.impact.runs_per_year == 1040
    assert after.step_analysis[0].minutes == 6
    assert not any(f.assumed for f in after.score.factors if f.key == "frequency")


def test_human_review_steps_save_little_time():
    ex = make_extraction([
        make_step("s1", action_type="decide_approve", stakes="consequential", output_nature="judgment", minutes=60),
        make_step("s2", action_type="decide_approve", stakes="consequential", output_nature="judgment", minutes=60),
    ])
    saved = analyze(ex).impact.saved_minutes_per_run
    assert saved.high <= 120 * 0.15


def test_unanalyzable_description_raises_questions():
    ex = make_extraction(steps=[], is_analyzable=False)
    with pytest.raises(InsufficientDetail) as err:
        analyze(ex)
    assert err.value.questions


@pytest.mark.parametrize("bad", [
    {"steps": [{"id": "s1"}]},                       # incomplete step
    {"frequency": "every so often"},                 # outside the vocabulary
    {"unexpected_field": True},                      # extra keys are rejected
])
def test_malformed_extraction_is_rejected(bad):
    base = load_extraction("weekly_sales_report").model_dump()
    with pytest.raises(ValidationError):
        Extraction.model_validate({**base, **bad})


def test_analyzable_process_needs_two_steps():
    with pytest.raises(ValidationError):
        make_extraction([make_step("s1")])


def test_duplicate_step_ids_rejected():
    with pytest.raises(ValidationError):
        make_extraction([make_step("s1"), make_step("s1")])
