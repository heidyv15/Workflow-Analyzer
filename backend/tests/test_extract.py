"""Extraction layer tests, using a fake client in place of the Anthropic SDK."""

import json
from types import SimpleNamespace

import pytest

from app.examples import load_extraction
from app.llm.extract import ClaudeExtractor, ExtractionError

VALID = load_extraction("weekly_sales_report").model_dump_json()


def reply(text: str, stop_reason: str = "end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        model="claude-opus-5-5",
        content=[SimpleNamespace(type="text", text=text)],
    )


class FakeClient:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls: list[dict] = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self.replies.pop(0)


def test_valid_output_returns_extraction_in_one_attempt():
    client = FakeClient(reply(VALID))
    run = ClaudeExtractor(client=client).extract("Every Monday I download...")
    assert run.attempts == 1
    assert run.extraction.process_name == "Weekly sales report"


def test_request_uses_structured_output_and_fallbacks():
    client = FakeClient(reply(VALID))
    ClaudeExtractor(client=client).extract("Every Monday I download...")
    call = client.calls[0]
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert call["fallbacks"] == "default"
    assert "<process_description>" in call["messages"][0]["content"]


def test_invalid_output_is_repaired_with_validation_errors():
    bad = json.loads(VALID)
    bad["steps"] = bad["steps"][:1]  # violates the two-step minimum
    client = FakeClient(reply(json.dumps(bad)), reply(VALID))

    run = ClaudeExtractor(client=client).extract("Every Monday I download...")

    assert run.attempts == 2
    repair_turn = client.calls[1]["messages"]
    assert [m["role"] for m in repair_turn] == ["user", "assistant", "user"]
    assert "at least two steps" in repair_turn[-1]["content"]


def test_two_invalid_outputs_raise_instead_of_showing_partial_results():
    client = FakeClient(reply("not json"), reply('{"is_analyzable": true}'))
    with pytest.raises(ExtractionError) as err:
        ClaudeExtractor(client=client).extract("Every Monday I download...")
    assert err.value.kind == "invalid_output"


def test_truncated_output_is_treated_as_invalid():
    client = FakeClient(reply(VALID[:200], stop_reason="max_tokens"), reply(VALID))
    assert ClaudeExtractor(client=client).extract("x" * 30).attempts == 2


def test_missing_credentials_is_reported_as_not_configured():
    class NoCredentials(FakeClient):
        def _create(self, **kwargs):
            raise TypeError('"Could not resolve authentication method. Expected one of api_key..."')

    with pytest.raises(ExtractionError) as err:
        ClaudeExtractor(client=NoCredentials()).extract("x" * 30)
    assert err.value.kind == "not_configured"


def test_refusal_is_reported_not_parsed():
    refused = SimpleNamespace(stop_reason="refusal", model="claude-opus-5-5", content=[])
    with pytest.raises(ExtractionError) as err:
        ClaudeExtractor(client=FakeClient(refused)).extract("x" * 30)
    assert err.value.kind == "refused"
