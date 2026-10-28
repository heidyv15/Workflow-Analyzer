import json
from types import SimpleNamespace

from app.engine import analyze
from app.examples import load_extraction
from app.llm.narrative import ClaudeNarrator, brief, check_grounding

ANALYSIS = analyze(load_extraction("weekly_sales_report"))  # score 77, 5 steps: 4 automated, 1 AI


def fake_client(text: str, stop_reason: str = "end_turn"):
    response = SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)])
    return SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=lambda **_: response)))


GOOD = (
    "Four of the five steps are rule-based and should run as a scheduled workflow. "
    "AI drafts only the summary of changes, and a person reviews it before it reaches management."
)


def test_grounded_summary_is_accepted():
    assert check_grounding(GOOD, ANALYSIS) == GOOD


def test_numbers_from_the_analysis_are_allowed():
    assert check_grounding("The process scores 77 out of 100, with 4 of 5 steps rule-based and well suited to automation.", ANALYSIS)


def test_invented_numbers_are_rejected():
    assert check_grounding("Automation covers 90 percent of the work, leaving judgment calls to the team lead.", ANALYSIS) is None


def test_time_claims_are_rejected():
    assert check_grounding("Automating this saves about three hours every week for the analyst who runs it.", ANALYSIS) is None


def test_em_dashes_are_normalized():
    out = check_grounding("Most steps are rule-based — only the summary needs AI, and a person reviews it.", ANALYSIS)
    assert out is not None and "—" not in out


def test_brief_contains_results_not_the_raw_description():
    facts = json.loads(brief(ANALYSIS).split("\n", 1)[1].rsplit("\n", 1)[0])
    assert facts["score"] == 77
    assert [s["classification"] for s in facts["steps"]].count("ai_assisted") == 1


def test_narrator_returns_validated_summary():
    narrator = ClaudeNarrator(client=fake_client(json.dumps({"summary": GOOD})))
    assert narrator.write(ANALYSIS) == GOOD


def test_narrator_failures_fall_back_to_none():
    assert ClaudeNarrator(client=fake_client("not json")).write(ANALYSIS) is None
    assert ClaudeNarrator(client=fake_client(json.dumps({"summary": GOOD}), "max_tokens")).write(ANALYSIS) is None
    assert ClaudeNarrator(client=fake_client(json.dumps({"summary": "Saves 3 hours a week overall for this team."}))).write(ANALYSIS) is None
