from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.models import NexusAuditEvent
from backend.app.schemas.nexus_contracts import RunCreate
from backend.app.services import nexus_workflow as workflow
from backend.app.strands_runtime import agent as agent_module
from backend.app.strands_runtime import toolbox as toolbox_module


def isolated_sessions():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_bounded_toolbox_reaches_human_boundary(monkeypatch):
    sessions = isolated_sessions()
    monkeypatch.setattr(toolbox_module, "SessionLocal", sessions)
    with sessions() as db:
        run = workflow.create_run(db, RunCreate())
        workflow_id = run.id

    toolbox = toolbox_module.toolbox
    assert toolbox.inspect(workflow_id)["state"] == "CREATED"
    assert toolbox.observe(workflow_id)["state"] == "OBSERVED"
    assert toolbox.forecast(workflow_id)["state"] == "PREDICTED"
    assert toolbox.build_twin(workflow_id)["state"] == "TWIN_READY"
    assert toolbox.simulate(workflow_id)["state"] == "SIMULATED"
    assert toolbox.rank_and_verify(workflow_id)["state"] == "VERIFIED"
    final = toolbox.prepare_brief(workflow_id)
    assert final["state"] == "AWAITING_HUMAN"
    assert final["result"]["approval_executed"] is False

    with sessions() as db:
        events = db.scalars(
            select(NexusAuditEvent).where(
                NexusAuditEvent.run_id == workflow_id,
                NexusAuditEvent.event_type == "strands.tool_completed",
            )
        ).all()
        assert len(events) == 7
        assert all(event.payload_json["production_action"] == "NOT_EXECUTED" for event in events)
        assert workflow.verify_audit(db, workflow_id)["valid"] is True


def test_offline_fallback_is_truthfully_labeled(monkeypatch):
    sessions = isolated_sessions()
    monkeypatch.setattr(toolbox_module, "SessionLocal", sessions)
    monkeypatch.setattr(agent_module, "SessionLocal", sessions)
    monkeypatch.setattr(agent_module.settings, "strands_enabled", False)
    monkeypatch.setattr(agent_module.settings, "strands_offline_fallback", True)
    with sessions() as db:
        run = workflow.create_run(db, RunCreate())
        workflow_id = run.id

    result = agent_module.invoke_workflow_agent(workflow_id, "Investigate this workflow end to end")

    assert result.runtime == "deterministic-offline-fallback"
    assert result.state == "AWAITING_HUMAN"
    assert result.surfaced_to_human is True
    assert result.production_action == "NOT_EXECUTED"
    assert result.tool_trace == [
        "inspect_operational_state",
        "collect_operational_evidence",
        "forecast_bottleneck",
        "build_bounded_digital_twin",
        "simulate_interventions",
        "rank_and_verify_interventions",
        "prepare_human_decision_brief",
    ]


def test_runtime_status_never_claims_live_agentcore_without_sdk():
    status = agent_module.runtime_status()
    assert status["provider"] == "Amazon Bedrock"
    assert status["production_action"] == "NOT_EXECUTED"
    assert isinstance(status["sdk_available"], bool)
    assert isinstance(status["agentcore_ready"], bool)
