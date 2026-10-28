"""Built-in example workflows.

Each example has a saved extraction (what the LLM step produces) so the demo
runs instantly, works without an API key, and doubles as a golden test case.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.schemas import Extraction

FIXTURES = Path(__file__).parent / "fixtures" / "extractions"


@dataclass(frozen=True)
class Example:
    id: str
    title: str
    tagline: str
    description: str


EXAMPLES = [
    Example(
        id="weekly_sales_report",
        title="Weekly Sales Report",
        tagline="Automation, AI, and human review together",
        description=(
            "Every Monday I download sales reports from three systems, combine them in Excel, "
            "compare this week's numbers to last week's, write a summary of major changes, "
            "and email the report to management."
        ),
    ),
    Example(
        id="intake_form",
        title="Form Intake Processing",
        tagline="Mostly traditional automation, no AI needed",
        description=(
            "Whenever someone submits our intake form, I copy their information into another "
            "spreadsheet, create a folder using their name, and send them the same confirmation email."
        ),
    ),
    Example(
        id="employee_review",
        title="Employee Situation Review",
        tagline="Judgment-heavy: stays with people",
        description=(
            "I review unusual employee situations and decide whether disciplinary action should be taken."
        ),
    ),
]
EXAMPLES_BY_ID = {e.id: e for e in EXAMPLES}


def load_extraction(example_id: str) -> Extraction:
    path = FIXTURES / f"{example_id}.json"
    return Extraction.model_validate(json.loads(path.read_text()))
