"""Suggested implementation architecture.

Tools come from a small catalog keyed by the organization's ecosystem
(detected from the systems the user mentioned) and the capabilities the
process actually needs. An LLM stage appears only when at least one step
was classified as AI-assisted.
"""

from __future__ import annotations

from typing import Literal

from app.schemas import ArchNode, Extraction, StepAssessment

Ecosystem = Literal["microsoft", "google", "neutral"]

# Product names only: generic words like "spreadsheet" or "shared drive" must not tip the balance.
MICROSOFT_HINTS = ("excel", "outlook", "sharepoint", "onedrive", "microsoft", "power bi", "dynamics", "office 365", "m365")
GOOGLE_HINTS = ("google", "gmail", "apps script")

CATALOG: dict[str, dict[Ecosystem, str]] = {
    "trigger_scheduled": {"microsoft": "Power Automate (scheduled flow)", "google": "n8n (schedule trigger)", "neutral": "n8n (schedule trigger)"},
    "trigger_event": {"microsoft": "Power Automate (event trigger)", "google": "n8n (Google Forms / Sheets trigger)", "neutral": "n8n (webhook trigger)"},
    "integration": {"microsoft": "Power Automate connectors + SharePoint", "google": "n8n Google Drive / Sheets nodes", "neutral": "n8n integrations / REST APIs"},
    "processing": {"microsoft": "Python (pandas) script", "google": "Python (pandas) script", "neutral": "Python (pandas) script"},
    "ai": {"microsoft": "LLM API with structured output (e.g. Azure OpenAI)", "google": "LLM API with structured output", "neutral": "LLM API with structured output"},
    "approval": {"microsoft": "Power Automate Approvals (Teams / Outlook)", "google": "n8n wait-for-approval step (email)", "neutral": "n8n wait-for-approval step (email / Slack)"},
    "email": {"microsoft": "Outlook", "google": "Gmail", "neutral": "Email service (SMTP / API)"},
    "files": {"microsoft": "SharePoint / OneDrive", "google": "Google Drive", "neutral": "Shared cloud storage"},
}


def detect_ecosystem(extraction: Extraction) -> Ecosystem:
    names = " | ".join(n.lower() for s in extraction.steps for n in s.systems)
    ms = sum(h in names for h in MICROSOFT_HINTS)
    google = sum(h in names for h in GOOGLE_HINTS)
    if ms > google:
        return "microsoft"
    if google > ms:
        return "google"
    return "neutral"


def build_architecture(extraction: Extraction, assessments: list[StepAssessment]) -> list[ArchNode]:
    eco = detect_ecosystem(extraction)
    by_id = {a.step_id: a for a in assessments}
    automated = [s for s in extraction.steps if by_id[s.id].classification == "traditional_automation"]
    ai = [s for s in extraction.steps if by_id[s.id].classification == "ai_assisted"]
    human = [s for s in extraction.steps if by_id[s.id].classification == "human_review"]
    actions = {s.action_type for s in automated}
    nodes: list[ArchNode] = []

    if extraction.trigger in ("scheduled", "event"):
        key = f"trigger_{extraction.trigger}"
        nodes.append(ArchNode(stage="Trigger", tool=CATALOG[key][eco], kind="trigger",
                              why="Runs automatically on a schedule or event. No code or AI needed."))
    else:
        nodes.append(ArchNode(stage="Trigger", tool="Manual start (form or button)", kind="trigger",
                              why="The process starts case by case, so a person starts it."))

    if actions & {"retrieve_data", "move_data"}:
        why = "Moves structured data between systems deterministically."
        if extraction.data_access == "manual_only":
            why += " Some systems lack APIs, so start with scheduled exports to a shared folder."
        nodes.append(ArchNode(stage="Data integration", tool=CATALOG["integration"][eco], kind="integration", why=why))

    if actions & {"transform_calculate", "compare_analyze"}:
        nodes.append(ArchNode(stage="Processing", tool=CATALOG["processing"][eco], kind="processing",
                              why="Calculations and comparisons stay deterministic, testable, and auditable."))

    if ai:
        nodes.append(ArchNode(stage="AI step", tool=CATALOG["ai"][eco], kind="ai",
                              why="Used only for: " + ", ".join(s.label.lower() for s in ai) + "."))

    if any(by_id[s.id].review_gate for s in ai):
        nodes.append(ArchNode(stage="Human approval", tool=CATALOG["approval"][eco], kind="human",
                              why="A person approves AI output before it is used or sent."))
    if human:
        nodes.append(ArchNode(stage="Human decision", tool="Decision by a person, with a prepared case file", kind="human",
                              why="Judgment-heavy steps stay with a person; automation only organizes the inputs."))

    if "file_management" in actions:
        nodes.append(ArchNode(stage="File storage", tool=CATALOG["files"][eco], kind="delivery",
                              why="Folders and files are created from a naming template."))
    if any(s.action_type == "communicate" for s in automated):
        nodes.append(ArchNode(stage="Delivery", tool=CATALOG["email"][eco], kind="delivery",
                              why="Sends the message through existing email; templated where possible."))

    return nodes
