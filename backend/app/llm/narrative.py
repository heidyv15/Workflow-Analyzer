"""Executive summary, written by the model from the engine's finished results.

This runs after scoring, so the model only puts decisions that were already
made into words. Its output is checked before use: it must stay short, cite no
numbers the analysis doesn't contain, and say nothing about time savings
(those are editable estimates and would go stale). On any failure the
engine's template summary is kept, so this step can never block a result.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Protocol

import anthropic
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.config import settings
from app.schemas import Analysis

log = logging.getLogger(__name__)

NARRATIVE_PROMPT_VERSION = "summary-v1"

SYSTEM_PROMPT = """\
You write the executive summary for an automation opportunity assessment. The \
analysis is already complete: a rules engine has classified every step and \
calculated the score. Your job is only to explain its results clearly to a manager.

Write 2 or 3 sentences, at most 70 words, covering: where rule-based automation \
fits, where AI is used and for what (or why it is not needed), and what stays \
with people.

- Use only facts from the analysis provided. Never change a classification, \
score, or risk level, and never add steps or tools.
- Do not mention time, hours, minutes, savings, or cost.
- Write plainly and specifically. No hype, no exclamation marks, no em dashes.
"""

TIME_WORDS = re.compile(r"\b(hours?|hrs?|minutes?|mins?|seconds?|savings?|saves?|cost)\b|\$", re.IGNORECASE)
NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")


class Narrative(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=40, max_length=600)


class Narrator(Protocol):
    def write(self, analysis: Analysis) -> str | None: ...


class ClaudeNarrator:
    def __init__(self, client: Any | None = None, model: str | None = None):
        self._client = client
        self.model = model or settings.model
        self._schema = anthropic.transform_schema(Narrative)

    def write(self, analysis: Analysis) -> str | None:
        try:
            if self._client is None:
                self._client = anthropic.Anthropic(timeout=settings.request_timeout_s, max_retries=1)
            response = self._client.beta.messages.create(
                model=self.model,
                max_tokens=4000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": brief(analysis)}],
                output_config={"effort": "low", "format": {"type": "json_schema", "schema": self._schema}},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
            if response.stop_reason != "end_turn":
                return None
            text = next((b.text for b in response.content if b.type == "text"), "")
            summary = Narrative.model_validate_json(text).summary
        except (anthropic.AnthropicError, ValidationError, TypeError) as e:
            log.warning("summary generation failed, keeping template: %s", e)
            return None
        return check_grounding(summary, analysis)


def brief(analysis: Analysis) -> str:
    """The facts the model may use, as compact JSON."""
    facts = {
        "process": analysis.process_name,
        "score": analysis.score.score,
        "band": analysis.score.band,
        "steps": [
            {"step": s.label, "classification": s.classification, "reviewed_by_person": s.review_gate}
            for s in analysis.step_analysis
        ],
        "added_by_engine": [n.label for n in analysis.future_workflow if n.inserted],
        "risk_level": analysis.risk.level,
        "risk_factors": [f.label for f in analysis.risk.factors],
        "tools": [n.tool for n in analysis.architecture],
    }
    return f"<analysis>\n{json.dumps(facts, indent=1)}\n</analysis>"


def check_grounding(summary: str, analysis: Analysis) -> str | None:
    """Reject summaries that cite time figures or numbers the analysis doesn't contain."""
    summary = summary.replace("—", ", ").replace(" ,", ",").strip()
    if TIME_WORDS.search(summary):
        log.warning("summary rejected: mentions time or cost")
        return None
    counts = [sum(s.classification == c for s in analysis.step_analysis)
              for c in ("traditional_automation", "ai_assisted", "human_review", "manual")]
    allowed = {analysis.score.score, len(analysis.step_analysis), *counts, 100}
    for match in NUMBER.findall(summary):
        if float(match) not in allowed:
            log.warning("summary rejected: unsupported number %s", match)
            return None
    return summary
