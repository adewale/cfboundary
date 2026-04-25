"""Cron/scheduled Worker scaffolding."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from gasket.ffi import SafeEnv

@dataclass
class ScheduledEvent:
    cron: str
    scheduled_time: int
    type: str = "scheduled"

class ScheduledHandler:
    async def __call__(self, event: Any, env: object, ctx: Any) -> None:
        scheduled = ScheduledEvent(
            cron=str(getattr(event, "cron", "")),
            scheduled_time=int(getattr(event, "scheduledTime", getattr(event, "scheduled_time", 0))),
        )
        await self.scheduled(scheduled, SafeEnv(env), ctx)

    async def scheduled(self, event: ScheduledEvent, env: SafeEnv, ctx: Any) -> None:
        raise NotImplementedError
