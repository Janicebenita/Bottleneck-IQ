from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import select

from ..database import SessionLocal
from ..models import NexusEvidence
from ..services import nexus_workflow as workflow


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "__table__"):
        return workflow.serialize(value)
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


class WorkflowToolbox:
    """Bounded operational tools exposed to Strands.

    Every method opens its own short database transaction. The toolbox can
    advance the persisted workflow, but deliberately exposes no approval,
    deployment, shell, infrastructure mutation, or production-action method.
    """

    def _call(self, workflow_id: int, tool_name: str, action: Callable[..., Any]) -> dict[str, Any]:
        with SessionLocal() as db:
            run = workflow.require_run(db, workflow_id)
            output = action(db, run)
            run = workflow.require_run(db, workflow_id)
            workflow.append_event(
                db,
                run,
                "strands.tool_completed",
                "strands-orchestrator",
                {
                    "tool": tool_name,
                    "resulting_state": run.state,
                    "production_action": "NOT_EXECUTED",
                },
            )
            return {
                "tool": tool_name,
                "workflow_id": workflow_id,
                "state": run.state,
                "result": _jsonable(output),
                "production_action": "NOT_EXECUTED",
            }

    def inspect(self, workflow_id: int) -> dict[str, Any]:
        def action(db: Any, run: Any) -> dict[str, Any]:
            evidence_count = len(
                db.scalars(select(NexusEvidence).where(NexusEvidence.run_id == run.id)).all()
            )
            return {
                "name": run.name,
                "state": run.state,
                "evidence_count": evidence_count,
                "has_forecast": bool(run.forecast_json),
                "has_twin": bool(run.twin_json),
                "scenario_count": len(run.scenarios_json),
                "recommended_candidate": run.tournament_json.get("recommended_candidate_id"),
            }

        return self._call(workflow_id, "inspect_operational_state", action)

    def observe(self, workflow_id: int) -> dict[str, Any]:
        def action(db: Any, run: Any) -> Any:
            if run.state == "CREATED":
                return workflow.observe(db, run)
            if run.state in {
                "OBSERVED", "PREDICTED", "TWIN_READY", "SIMULATED", "TOURNAMENT_READY",
                "VERIFIED", "IMPACT_READY", "AWAITING_HUMAN", "DECIDED",
            }:
                return {"already_completed": True, "state": run.state}
            raise ValueError(f"Evidence collection cannot run from state {run.state}")

        return self._call(workflow_id, "collect_operational_evidence", action)

    def forecast(self, workflow_id: int) -> dict[str, Any]:
        def action(db: Any, run: Any) -> Any:
            if run.state == "OBSERVED":
                return workflow.predict(db, run)
            if run.forecast_json:
                return run.forecast_json
            raise ValueError("Forecasting requires collected operational evidence")

        return self._call(workflow_id, "forecast_bottleneck", action)

    def build_twin(self, workflow_id: int) -> dict[str, Any]:
        def action(db: Any, run: Any) -> Any:
            if run.state == "PREDICTED":
                return workflow.build_twin(db, run)
            if run.twin_json:
                return run.twin_json
            raise ValueError("Digital Twin creation requires a persisted forecast")

        return self._call(workflow_id, "build_bounded_digital_twin", action)

    def simulate(self, workflow_id: int) -> dict[str, Any]:
        def action(db: Any, run: Any) -> Any:
            if run.state == "TWIN_READY":
                return workflow.simulate(db, run)
            if run.scenarios_json:
                return run.scenarios_json
            raise ValueError("Scenario simulation requires a version-locked Digital Twin")

        return self._call(workflow_id, "simulate_interventions", action)

    def rank_and_verify(self, workflow_id: int) -> dict[str, Any]:
        def action(db: Any, run: Any) -> Any:
            if run.state == "SIMULATED":
                workflow.tournament(db, run)
            if run.state == "TOURNAMENT_READY":
                workflow.verify(db, run)
            if run.state not in {"VERIFIED", "IMPACT_READY", "AWAITING_HUMAN", "DECIDED"}:
                raise ValueError("Verification requires completed counterfactual simulations")
            return {
                "recommended_candidate": run.tournament_json.get("recommended_candidate_id"),
                "candidates": run.tournament_json.get("candidates", []),
                "verified": True,
            }

        return self._call(workflow_id, "rank_and_verify_interventions", action)

    def prepare_brief(self, workflow_id: int) -> dict[str, Any]:
        def action(db: Any, run: Any) -> Any:
            if run.state == "VERIFIED":
                workflow.impact(db, run)
            if run.state == "IMPACT_READY":
                workflow.recommend(db, run)
            if run.state not in {"AWAITING_HUMAN", "DECIDED"}:
                raise ValueError("A human decision brief requires successful verification")
            return {
                "brief": run.recommendation_json,
                "impact": run.impact_json,
                "surface_to_human": run.state == "AWAITING_HUMAN",
                "approval_executed": False,
            }

        return self._call(workflow_id, "prepare_human_decision_brief", action)


toolbox = WorkflowToolbox()
