from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import nexus_workflow as workflow
from ..strands_runtime import invoke_workflow_agent, runtime_status
from ..strands_runtime.agent import StrandsInvocationRequest
from ..strands_runtime.background import run_monitor_once

router = APIRouter(prefix="/api/v1", tags=["AWS Strands HumanGuard"])
Db = Annotated[Session, Depends(get_db)]


@router.get("/strands/status")
def strands_status() -> dict[str, Any]:
    return runtime_status()


@router.post("/workflows/{workflow_id}/strands/invoke")
def invoke_strands(workflow_id: int, payload: StrandsInvocationRequest, db: Db) -> Any:
    try:
        workflow.require_run(db, workflow_id)
        return invoke_workflow_agent(workflow_id, payload.prompt)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/strands/background/tick")
def background_tick() -> dict[str, Any]:
    try:
        return run_monitor_once()
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
