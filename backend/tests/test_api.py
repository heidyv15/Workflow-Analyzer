import pytest
from fastapi.testclient import TestClient

from app.examples import load_extraction
from app.llm.extract import ExtractionError, ExtractionRun
from app.main import app, get_extractor, get_limiter, get_narrator
from app.ratelimit import RateLimiter
from tests.factories import make_extraction

DESCRIPTION = "Every Monday I download sales reports from three systems and email a summary."


class StubExtractor:
    def __init__(self, result):
        self.result = result

    def extract(self, description):
        if isinstance(self.result, Exception):
            raise self.result
        return ExtractionRun(self.result, "claude-opus-5-5", "extract-v1", 1, 1234)


class StubNarrator:
    def __init__(self, summary=None):
        self.summary = summary

    def write(self, analysis):
        return self.summary


@pytest.fixture
def client():
    app.dependency_overrides[get_narrator] = lambda: StubNarrator()
    limiter = RateLimiter(per_visitor_per_hour=1000, global_per_day=1000)
    app.dependency_overrides[get_limiter] = lambda: limiter
    yield TestClient(app)
    app.dependency_overrides.clear()


def use(result):
    app.dependency_overrides[get_extractor] = lambda: StubExtractor(result)


def test_examples_list_and_cached_analysis(client):
    examples = client.get("/api/examples").json()
    assert [e["id"] for e in examples] == ["weekly_sales_report", "intake_form", "employee_review"]

    body = client.get("/api/examples/intake_form/analysis").json()
    assert body["status"] == "complete"
    assert body["run"]["source"] == "example"
    assert body["analysis"]["ai_used_for"] == []


def test_unknown_example_404(client):
    assert client.get("/api/examples/nope/analysis").status_code == 404


def test_analyze_returns_analysis_and_extraction(client):
    use(load_extraction("weekly_sales_report"))
    body = client.post("/api/analyze", json={"description": DESCRIPTION}).json()
    assert body["status"] == "complete"
    assert body["analysis"]["score"]["band"] == "high"
    assert body["extraction"]["process_name"] == "Weekly sales report"
    assert body["run"] == {
        "source": "live", "engine_version": "1.0.0", "prompt_version": "extract-v1",
        "model": "claude-opus-5-5", "attempts": 1, "latency_ms": 1234,
    }


def test_vague_description_asks_questions(client):
    use(make_extraction(steps=[], is_analyzable=False))
    body = client.post("/api/analyze", json={"description": "I do some stuff with files sometimes."}).json()
    assert body["status"] == "needs_detail"
    assert body["analysis"] is None
    assert body["questions"]


@pytest.mark.parametrize("description", ["too short", "x" * 4001])
def test_description_length_is_enforced(client, description):
    assert client.post("/api/analyze", json={"description": description}).status_code == 422


@pytest.mark.parametrize("kind,status", [
    ("not_configured", 503), ("unavailable", 503), ("rate_limited", 429),
    ("refused", 422), ("invalid_output", 502),
])
def test_extraction_errors_map_to_friendly_responses(client, kind, status):
    use(ExtractionError(kind, "internal detail"))
    res = client.post("/api/analyze", json={"description": DESCRIPTION})
    assert res.status_code == status
    detail = res.json()["detail"]
    assert detail["code"] == kind
    assert "internal detail" not in detail["message"]


def test_recompute_applies_overrides_without_llm(client):
    extraction = load_extraction("intake_form").model_dump()
    res = client.post("/api/recompute", json={
        "extraction": extraction,
        "overrides": {"runs_per_year": 520, "step_minutes": {"s1": 5}},
    })
    assert res.status_code == 200
    assert res.json()["impact"]["saved_hours_per_year"] is not None


def test_recompute_rejects_unknown_step_ids(client):
    extraction = load_extraction("intake_form").model_dump()
    res = client.post("/api/recompute", json={"extraction": extraction, "overrides": {"step_minutes": {"s9": 5}}})
    assert res.status_code == 422


def test_model_summary_replaces_template_when_available(client):
    use(load_extraction("weekly_sales_report"))
    app.dependency_overrides[get_narrator] = lambda: StubNarrator("A grounded summary written from the engine's results.")
    analysis = client.post("/api/analyze", json={"description": DESCRIPTION}).json()["analysis"]
    assert analysis["summary"] == "A grounded summary written from the engine's results."
    assert analysis["meta"]["summary_source"] == "model"


def test_template_summary_kept_when_narrator_declines(client):
    use(load_extraction("weekly_sales_report"))
    analysis = client.post("/api/analyze", json={"description": DESCRIPTION}).json()["analysis"]
    assert analysis["summary"].startswith("Strong automation candidate.")
    assert analysis["meta"]["summary_source"] == "template"


def test_methodology_is_generated_from_engine_constants(client):
    m = client.get("/api/methodology").json()
    assert sum(f["weight"] for f in m["factors"]) == 100
    assert [r["id"] for r in m["rules"]] == ["R1", "R2", "R3", "R4", "R5", "R6"]
    assert m["bands"][0] == {"band": "high", "min_score": 75}


def test_live_analyses_are_rate_limited(client):
    use(load_extraction("weekly_sales_report"))
    limiter = RateLimiter(per_visitor_per_hour=2, global_per_day=100)
    app.dependency_overrides[get_limiter] = lambda: limiter
    codes = [client.post("/api/analyze", json={"description": DESCRIPTION}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
    # Examples never count against the limit.
    assert client.get("/api/examples/intake_form/analysis").status_code == 200


def test_vercel_visitors_are_identified_by_real_ip(client, monkeypatch):
    import dataclasses

    import app.main as main

    use(load_extraction("weekly_sales_report"))
    monkeypatch.setattr(main, "settings", dataclasses.replace(main.settings, on_vercel=True))
    limiter = RateLimiter(per_visitor_per_hour=1, global_per_day=100)
    app.dependency_overrides[get_limiter] = lambda: limiter
    post = lambda ip: client.post("/api/analyze", json={"description": DESCRIPTION}, headers={"x-real-ip": ip}).status_code  # noqa: E731
    assert [post("203.0.113.1"), post("203.0.113.1"), post("203.0.113.2")] == [200, 429, 200]
