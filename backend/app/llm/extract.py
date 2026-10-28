"""The single LLM call: description in, validated `Extraction` out.

The response is constrained to the Extraction JSON schema (structured outputs),
then validated again with Pydantic, which also enforces rules a JSON schema
can't express (e.g. at least two steps, unique ids). If validation fails, the
errors are sent back once for a repair attempt. Anything else surfaces as a
typed `ExtractionError` so the API never returns a half-built analysis.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Literal, Protocol

import anthropic
from pydantic import ValidationError

from app.config import settings
from app.llm.prompt import PROMPT_VERSION, SYSTEM_PROMPT, repair_message, user_message
from app.schemas import Extraction

MAX_ATTEMPTS = 2  # one original call plus one repair
FALLBACK_BETA = "server-side-fallback-2026-07-01"

ErrorKind = Literal["not_configured", "unavailable", "rate_limited", "refused", "invalid_output"]


class ExtractionError(Exception):
    def __init__(self, kind: ErrorKind, detail: str):
        super().__init__(detail)
        self.kind = kind
        self.detail = detail


@dataclass(frozen=True)
class ExtractionRun:
    extraction: Extraction
    model: str
    prompt_version: str
    attempts: int
    latency_ms: int


class Extractor(Protocol):
    def extract(self, description: str) -> ExtractionRun: ...


class ClaudeExtractor:
    def __init__(self, client: Any | None = None, model: str | None = None, effort: str | None = None):
        self._client = client
        self.model = model or settings.model
        self.effort = effort or settings.effort
        self._schema = anthropic.transform_schema(Extraction)

    @property
    def client(self) -> Any:
        if self._client is None:
            try:
                self._client = anthropic.Anthropic(timeout=settings.request_timeout_s, max_retries=2)
            except anthropic.AnthropicError as e:
                raise ExtractionError("not_configured", "No Anthropic API credentials are configured.") from e
        return self._client

    def extract(self, description: str) -> ExtractionRun:
        started = time.monotonic()
        messages: list[dict[str, Any]] = [{"role": "user", "content": user_message(description)}]

        for attempt in range(1, MAX_ATTEMPTS + 1):
            response = self._call(messages)

            if response.stop_reason == "refusal":
                raise ExtractionError("refused", "The model declined to analyze this description.")

            text = next((b.text for b in response.content if b.type == "text"), "")
            try:
                if response.stop_reason == "max_tokens":
                    raise ValueError("output was truncated")
                extraction = Extraction.model_validate_json(text)
            except (ValidationError, ValueError) as e:
                if attempt == MAX_ATTEMPTS:
                    raise ExtractionError("invalid_output", f"Model output failed validation: {_short(e)}") from e
                # Append the full assistant turn (thinking blocks included) so the history stays valid.
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": repair_message(_short(e))})
                continue

            return ExtractionRun(
                extraction=extraction,
                model=response.model,
                prompt_version=PROMPT_VERSION,
                attempts=attempt,
                latency_ms=int((time.monotonic() - started) * 1000),
            )

        raise AssertionError("unreachable")

    def _call(self, messages: list[dict[str, Any]]) -> Any:
        try:
            return self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                messages=messages,
                output_config={
                    "effort": self.effort,
                    "format": {"type": "json_schema", "schema": self._schema},
                },
                # Server-side fallback: if a safety classifier declines, the API retries on another model.
                betas=[FALLBACK_BETA],
                fallbacks="default",
            )
        except anthropic.AuthenticationError as e:
            raise ExtractionError("not_configured", "The Anthropic API key is missing or invalid.") from e
        except anthropic.RateLimitError as e:
            raise ExtractionError("rate_limited", "The model is rate limited. Try again shortly.") from e
        except anthropic.BadRequestError as e:
            raise ExtractionError("unavailable", f"The model rejected the request: {e.message}") from e
        except anthropic.APIStatusError as e:
            raise ExtractionError("unavailable", f"Model service error ({e.status_code}).") from e
        except anthropic.APIConnectionError as e:
            raise ExtractionError("unavailable", "Could not reach the model service.") from e
        except anthropic.AnthropicError as e:
            raise ExtractionError("unavailable", f"Model client error: {e}") from e
        except TypeError as e:
            # The SDK raises TypeError before sending anything when no credentials can be resolved.
            if "authentication" not in str(e).lower():
                raise
            raise ExtractionError("not_configured", "No Anthropic API credentials are configured.") from e


def _short(error: Exception, limit: int = 1500) -> str:
    if isinstance(error, ValidationError):
        lines = [f"{'.'.join(str(p) for p in err['loc']) or 'root'}: {err['msg']}" for err in error.errors()[:15]]
        text = "\n".join(lines)
    else:
        text = str(error)
    return text[:limit]
