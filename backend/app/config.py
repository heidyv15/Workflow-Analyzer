"""Runtime settings, read from the environment (and a local .env file in development)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    model: str = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
    effort: str = os.getenv("ANTHROPIC_EFFORT", "medium")
    request_timeout_s: float = float(os.getenv("ANTHROPIC_TIMEOUT_S", "90"))
    analyses_per_visitor_per_hour: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "10"))
    analyses_per_day: int = int(os.getenv("DAILY_ANALYSIS_LIMIT", "200"))
    # On Vercel the client address arrives in the x-real-ip header set by Vercel's edge.
    on_vercel: bool = bool(os.getenv("VERCEL"))
    # Built frontend to serve in production; ignored when the folder doesn't exist.
    static_dir: Path = Path(os.getenv("STATIC_DIR", str(Path(__file__).resolve().parents[2] / "frontend" / "dist")))
    allowed_origins: list[str] = field(
        default_factory=lambda: [
            o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()
        ]
    )


settings = Settings()

# Input limits for a process description.
MIN_DESCRIPTION_CHARS = 20
MAX_DESCRIPTION_CHARS = 4000
