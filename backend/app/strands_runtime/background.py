from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import select

from ..config import settings
from ..database import SessionLocal
from ..models import NexusRun
from ..schemas.nexus_contracts import RunCreate
from ..services import nexus_workflow as workflow
from .agent import invoke_workflow_agent

_monitor_task: asyncio.Task[None] | None = None


def run_monitor_once() -> dict[str, Any]:
    """Process the newest actionable workflow and remain quiet otherwise."""
    with SessionLocal() as db:
        run = db.scalar(select(NexusRun).order_by(NexusRun.id.desc()))
        if run is None and settings.background_auto_seed:
            run = workflow.create_run(db, RunCreate(name="Background Payment Service monitor"))
        if run is None:
            return {"status": "quiet", "reason": "no_workflow", "production_action": "NOT_EXECUTED"}
        workflow_id = run.id
        state = run.state
    if state in {"AWAITING_HUMAN", "DECIDED"}:
        return {
            "status": "quiet",
            "reason": "no_new_decision",
            "workflow_id": workflow_id,
            "state": state,
            "production_action": "NOT_EXECUTED",
        }
    result = invoke_workflow_agent(
        workflow_id,
        "Monitor this operational workflow silently. Investigate end to end and notify a human only if a verified decision is required.",
    )
    return {"status": "human_decision_required" if result.surfaced_to_human else "processed", **result.model_dump()}


async def _monitor_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(run_monitor_once)
        except Exception:
            # The monitor is fail-safe: an unavailable model or database never
            # weakens policy and is retried on the next bounded interval.
            pass
        await asyncio.sleep(settings.background_monitor_interval_seconds)


def start_background_monitor() -> None:
    global _monitor_task
    if settings.background_monitor_enabled and (_monitor_task is None or _monitor_task.done()):
        _monitor_task = asyncio.create_task(_monitor_loop(), name="bottleneck-iq-strands-monitor")


async def stop_background_monitor() -> None:
    global _monitor_task
    if _monitor_task is not None:
        _monitor_task.cancel()
        try:
            await _monitor_task
        except asyncio.CancelledError:
            pass
        _monitor_task = None
