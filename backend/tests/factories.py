"""Small builders so unit tests only spell out the facts they care about."""

from __future__ import annotations

from app.schemas import ExtractedStep, Extraction

_STEP_DEFAULTS = dict(
    label="Step",
    future_label="Automated step",
    action_type="transform_calculate",
    input_data="structured",
    output_nature="deterministic",
    requires_judgment=False,
    stakes="none",
    external_facing=False,
    sensitivity=[],
    minutes=10,
    minutes_source="stated",
    systems=[],
)


def make_step(id: str = "s1", **overrides) -> ExtractedStep:
    return ExtractedStep(**{**_STEP_DEFAULTS, "id": id, **overrides})


def make_extraction(steps: list[ExtractedStep] | None = None, **overrides) -> Extraction:
    steps = steps or [make_step("s1"), make_step("s2")]
    defaults = dict(
        is_analyzable=True,
        process_name="Test process",
        trigger="scheduled",
        frequency="weekly",
        frequency_source="stated",
        consistency="standardized",
        data_access="connected",
        steps=steps,
    )
    return Extraction(**{**defaults, **overrides})
