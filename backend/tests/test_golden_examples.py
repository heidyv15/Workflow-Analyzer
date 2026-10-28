"""Golden tests: the three built-in examples must produce meaningfully different outcomes.

These run on saved extractions, so they test the engine's judgment without any
LLM call. If a scoring or rule change breaks one of these, the product's core
claim ("it doesn't just say 'use AI' for everything") is broken.
"""

import pytest

from app.engine import analyze
from app.examples import EXAMPLES, load_extraction


def classes(analysis):
    return [a.classification for a in analysis.step_analysis]


def categories(nodes):
    return [n.category for n in nodes]


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda e: e.id)
def test_every_example_produces_a_valid_analysis(example):
    analysis = analyze(load_extraction(example.id))
    assert 0 <= analysis.score.score <= 100
    assert len(analysis.step_analysis) == len(analysis.current_workflow)


class TestWeeklySalesReport:
    """Mix of traditional automation, AI, and human review."""

    @pytest.fixture
    def analysis(self):
        return analyze(load_extraction("weekly_sales_report"))

    def test_high_potential(self, analysis):
        assert analysis.score.band == "high"

    def test_data_steps_are_deterministic_and_only_the_summary_uses_ai(self, analysis):
        assert classes(analysis) == [
            "traditional_automation",  # download
            "traditional_automation",  # combine in Excel
            "traditional_automation",  # week-over-week comparison
            "ai_assisted",             # write summary
            "traditional_automation",  # email
        ]

    def test_human_review_gate_sits_between_ai_summary_and_email(self, analysis):
        labels = [n.label for n in analysis.future_workflow]
        summary = labels.index("Draft summary of key changes")
        send = labels.index("Send report to management")
        assert "Human review" in labels[summary + 1:send]

    def test_inserts_trigger_and_validation(self, analysis):
        first = analysis.future_workflow[0]
        assert first.label == "Scheduled trigger" and first.inserted
        assert any(n.id == "f-validate" for n in analysis.future_workflow)

    def test_moderate_risk(self, analysis):
        assert analysis.risk.level == "moderate"

    def test_microsoft_stack_with_ai_and_approval(self, analysis):
        tools = " ".join(n.tool for n in analysis.architecture)
        kinds = [n.kind for n in analysis.architecture]
        assert "Power Automate" in tools and "Outlook" in tools
        assert "ai" in kinds and "human" in kinds

    def test_impact_is_a_range_with_annual_total(self, analysis):
        impact = analysis.impact
        assert impact.saved_minutes_per_run.low < impact.saved_minutes_per_run.high
        assert impact.runs_per_year == 52
        assert impact.saved_hours_per_year is not None
        assert impact.confidence == "medium"  # durations inferred, frequency stated


class TestIntakeForm:
    """Highly automatable with no AI at all."""

    @pytest.fixture
    def analysis(self):
        return analyze(load_extraction("intake_form"))

    def test_high_potential_without_ai(self, analysis):
        assert analysis.score.band == "high"
        assert set(classes(analysis)) == {"traditional_automation"}
        assert analysis.ai_used_for == []
        assert "ai_assisted" not in categories(analysis.future_workflow)
        assert "ai" not in [n.kind for n in analysis.architecture]

    def test_low_risk(self, analysis):
        assert analysis.risk.level == "low"

    def test_unknown_frequency_withholds_annual_savings_and_asks(self, analysis):
        assert analysis.impact.saved_hours_per_year is None
        assert any(m.field == "frequency" for m in analysis.missing_information)
        frequency = next(f for f in analysis.score.factors if f.key == "frequency")
        assert frequency.assumed


class TestEmployeeReview:
    """Judgment-heavy: the decision stays with people."""

    @pytest.fixture
    def analysis(self):
        return analyze(load_extraction("employee_review"))

    def test_keep_human_led(self, analysis):
        assert analysis.score.band == "keep_human_led"
        assert analysis.score.score < 25

    def test_review_and_decision_stay_human(self, analysis):
        assert classes(analysis)[1:] == ["human_review", "human_review"]
        assert analysis.step_analysis[2].rule_id == "R1"

    def test_no_ai_and_high_risk(self, analysis):
        assert analysis.ai_used_for == []
        assert analysis.risk.level == "high"


def test_examples_rank_in_expected_order():
    scores = {e.id: analyze(load_extraction(e.id)).score.score for e in EXAMPLES}
    assert scores["employee_review"] < 25 <= 75 <= min(scores["weekly_sales_report"], scores["intake_form"])
