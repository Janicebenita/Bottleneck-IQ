"""Amazon Bedrock AgentCore Runtime entrypoint for Bottleneck IQ HumanGuard."""

from typing import Any

from bedrock_agentcore import BedrockAgentCoreApp
from sqlalchemy import select

from backend.app.database import Base, SessionLocal, engine
from backend.app.models import NexusRun
from backend.app.schemas.nexus_contracts import RunCreate
from backend.app.services import nexus_workflow as workflow
from backend.app.strands_runtime import invoke_workflow_agent
from backend.app.strands_runtime.agent import StrandsInvocationRequest

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Investigate one workflow and return only a verified human decision brief."""
    Base.metadata.create_all(engine)
    request = StrandsInvocationRequest(prompt=payload.get("prompt") or StrandsInvocationRequest().prompt)
    workflow_id = payload.get("workflow_id")
    with SessionLocal() as db:
        run = db.get(NexusRun, int(workflow_id)) if workflow_id is not None else None
        if run is None:
            run = db.scalar(select(NexusRun).order_by(NexusRun.id.desc()))
        if run is None:
            run = workflow.create_run(db, RunCreate(name="AgentCore background reliability monitor"))
        workflow_id = run.id
    result = invoke_workflow_agent(int(workflow_id), request.prompt)
    return result.model_dump(mode="json")


if __name__ == "__main__":
    app.run()
