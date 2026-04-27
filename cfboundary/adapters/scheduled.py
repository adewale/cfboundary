"""Small helpers for scheduled Worker events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ScheduledEvent:
    cron: str
    scheduled_time: int
    type: str = "scheduled"


def scheduled_event_from_js(event: Any) -> ScheduledEvent:
    """Normalize a Workers scheduled event object to a Python dataclass."""
    return ScheduledEvent(
        cron=str(getattr(event, "cron", "")),
        scheduled_time=int(getattr(event, "scheduledTime", getattr(event, "scheduled_time", 0))),
    )
