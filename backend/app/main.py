"""HTTP API.

    GET  /api/health                     liveness + engine/prompt versions
    GET  /api/examples                   built-in example workflows
    GET  /api/examples/{id}/analysis     example analysis from a saved extraction (no LLM call)
    POST /api/analyze                    description -> LLM extraction -> engine -> analysis
    POST /api/recompute                  extraction + edited assumptions -> analysis (no LLM call)
    GET  /api/methodology                the scoring model, generated from the engine's constants

In production the same app also serves the built frontend from `settings.static_dir`.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from app.config import MAX_DESCRIPTION_CHARS, MIN_DESCRIPTION_CHARS, settings
from app.engine import ENGINE_VERSION, InsufficientDetail, analyze
from app.engine.methodology import describe as describe_methodology
from app.examples import EXAMPLES, EXAMPLES_BY_ID, load_extraction
from app.llm.extract import ClaudeExtractor, ExtractionError, Extractor
from app.llm.narrative import ClaudeNarrator, Narrator
from app.llm.prompt import PROMPT_VERSION
from app.ratelimit import RateLimiter
from app.schemas import Analysis, Extraction, MissingInfo, Overrides

app = FastAPI(title="AI Workflow Opportunity Analyzer", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# --------------------------------------------------------------------------
# Request / response models
# --------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = Field(min_length=MIN_DESCRIPTION_CHARS, max_length=MAX_DESCRIPTION_CHARS)


class RecomputeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    extraction: Extraction
    overrides: Overrides = Overrides()


class RunInfo(BaseModel):
    source: Literal["live", "example"]
    engine_version: str
    prompt_version: str | None = None
    model: str | None = None
    attempts: int | None = None
    latency_ms: int | None = None


class AnalyzeResponse(BaseModel):
    status: Literal["complete", "needs_detail"]
    analysis: Analysis | None = None
    # Returned so the client can send it back to /api/recompute when assumptions change.
    extraction: Extraction | None = None
    questions: list[MissingInfo] = []
    run: RunInfo


class ExampleSummary(BaseModel):
    id: str
    title: str
    tagline: str
    description: str


ERROR_STATUS = {
    "not_configured": 503,
    "unavailable": 503,
    "rate_limited": 429,
    "refused": 422,
    "invalid_output": 502,
}
ERROR_MESSAGE = {
    "not_configured": "The analyzer isn't connected to a model right now. The built-in examples still work.",
    "unavailable": "The model service is temporarily unavailable. Please try again.",
    "rate_limited": "Too many requests right now. Please wait a moment and try again.",
    "visitor_limit": "You've reached the hourly limit for live analyses. The built-in examples are always available.",
    "daily_limit": "This demo has reached its daily limit for live analyses. The built-in examples are always available.",
    "refused": "This description couldn't be analyzed. Try describing the business process in more neutral terms.",
    "invalid_output": "The analysis didn't pass validation, so nothing was shown. Please try again.",
}


# --------------------------------------------------------------------------
# Dependencies
# --------------------------------------------------------------------------


@lru_cache
def _default_extractor() -> ClaudeExtractor:
    return ClaudeExtractor()


def get_extractor() -> Extractor:
    return _default_extractor()


@lru_cache
def _default_narrator() -> ClaudeNarrator:
    return ClaudeNarrator()


def get_narrator() -> Narrator:
    return _default_narrator()


_limiter = RateLimiter(settings.analyses_per_visitor_per_hour, settings.analyses_per_day)


def get_limiter() -> RateLimiter:
    return _limiter


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


def visitor_id(request: Request) -> str:
    # Vercel sets x-real-ip at its edge; elsewhere uvicorn's --proxy-headers fills request.client.
    if settings.on_vercel and request.headers.get("x-real-ip"):
        return request.headers["x-real-ip"]
    return request.client.host if request.client else "unknown"


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "engine_version": ENGINE_VERSION, "prompt_version": PROMPT_VERSION}


@app.get("/api/examples", response_model=list[ExampleSummary])
def list_examples() -> list[ExampleSummary]:
    return [ExampleSummary(**e.__dict__) for e in EXAMPLES]


@app.get("/api/examples/{example_id}/analysis", response_model=AnalyzeResponse)
def example_analysis(example_id: str) -> AnalyzeResponse:
    if example_id not in EXAMPLES_BY_ID:
        raise HTTPException(status_code=404, detail="Unknown example.")
    extraction = load_extraction(example_id)
    return AnalyzeResponse(
        status="complete",
        analysis=analyze(extraction),
        extraction=extraction,
        run=RunInfo(source="example", engine_version=ENGINE_VERSION),
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze_description(
    req: AnalyzeRequest,
    request: Request,
    limiter: RateLimiter = Depends(get_limiter),
    extractor: Extractor = Depends(get_extractor),
    narrator: Narrator = Depends(get_narrator),
) -> AnalyzeResponse:
    blocked = limiter.check(visitor_id(request))
    if blocked:
        code = f"{blocked}_limit"
        raise HTTPException(status_code=429, detail={"code": "rate_limited", "message": ERROR_MESSAGE[code]})

    # Sync handler: FastAPI runs it in a worker thread, so the blocking SDK call is fine here.
    try:
        run = extractor.extract(req.description.strip())
    except ExtractionError as e:
        raise HTTPException(
            status_code=ERROR_STATUS[e.kind],
            detail={"code": e.kind, "message": ERROR_MESSAGE[e.kind]},
        ) from e

    info = RunInfo(
        source="live",
        engine_version=ENGINE_VERSION,
        prompt_version=run.prompt_version,
        model=run.model,
        attempts=run.attempts,
        latency_ms=run.latency_ms,
    )
    try:
        analysis = analyze(run.extraction)
    except InsufficientDetail as e:
        return AnalyzeResponse(status="needs_detail", questions=e.questions, run=info)

    # Optional: the model rewrites the template summary from the finished results.
    summary = narrator.write(analysis)
    if summary:
        analysis = analysis.model_copy(update={
            "summary": summary,
            "meta": analysis.meta.model_copy(update={"summary_source": "model"}),
        })
    return AnalyzeResponse(status="complete", analysis=analysis, extraction=run.extraction, run=info)


@app.get("/api/methodology")
def methodology() -> dict:
    return describe_methodology()


@app.post("/api/recompute", response_model=Analysis)
def recompute(req: RecomputeRequest) -> Analysis:
    unknown = set(req.overrides.step_minutes) - {s.id for s in req.extraction.steps}
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown step ids: {sorted(unknown)}")
    try:
        return analyze(req.extraction, req.overrides)
    except InsufficientDetail as e:
        raise HTTPException(status_code=422, detail="This extraction can't be analyzed.") from e


# Mounted last so every /api route above takes precedence.
if settings.static_dir.is_dir():
    app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="web")
