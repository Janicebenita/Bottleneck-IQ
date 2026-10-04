from __future__ import annotations

from importlib import import_module
from importlib.util import find_spec
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field

from ..config import settings
from ..database import SessionLocal
from ..services import nexus_workflow as workflow
from .toolbox import toolbox

try:
    _strands = import_module("strands")
    _strands_models = import_module("strands.models")
    AgentClass: Any = _strands.Agent
    BedrockModelClass: Any = _strands_models.BedrockModel
    tool_decorator: Any = _strands.tool
    STRANDS_AVAILABLE = True
except ImportError:  # Keeps health endpoints truthful before optional setup completes.
    AgentClass = None
    BedrockModelClass = None
    tool_decorator = None
    STRANDS_AVAILABLE = False


class StrandsInvocationRequest(BaseModel):
    prompt: str = Field(
        default=(
            "Investigate this workflow end to end. Use the bounded tools in order, verify all "
            "mandatory gates, and surface a concise decision brief only when human review is required."
        ),
        min_length=10,
        max_length=2000,
    )


class StrandsRunResult(BaseModel):
    workflow_id: int
    runtime: Literal["strands-bedrock", "deterministic-offline-fallback"]
    model_id: str
    state: str
    surfaced_to_human: bool
    response: str
    tool_trace: list[str]
    production_action: Literal["NOT_EXECUTED"] = "NOT_EXECUTED"


def _state(context: Any) -> dict[str, Any]:
    value = getattr(context, "invocation_state", None)
    return value if isinstance(value, dict) else {}


def _invoke_tool(context: Any, name: str, action: Callable[[int], dict[str, Any]]) -> dict[str, Any]:
    state = _state(context)
    workflow_id = int(state["workflow_id"])
    trace = state.setdefault("tool_trace", [])
    trace.append(name)
    return action(workflow_id)


def _decorate(function: Callable[..., dict[str, Any]]) -> Any:
    return tool_decorator(context=True)(function) if tool_decorator is not None else function


def inspect_operational_state(tool_context: Any) -> dict[str, Any]:
    """Inspect persisted workflow state and evidence without changing production systems."""
    return _invoke_tool(tool_context, "inspect_operational_state", toolbox.inspect)


def collect_operational_evidence(tool_context: Any) -> dict[str, Any]:
    """Collect normalized telemetry, topology, configuration, and SLO evidence."""
    return _invoke_tool(tool_context, "collect_operational_evidence", toolbox.observe)


def forecast_bottleneck(tool_context: Any) -> dict[str, Any]:
    """Run the transparent bounded capacity forecast using persisted evidence."""
    return _invoke_tool(tool_context, "forecast_bottleneck", toolbox.forecast)


def build_bounded_digital_twin(tool_context: Any) -> dict[str, Any]:
    """Create a version-locked, content-hashed operational Digital Twin."""
    return _invoke_tool(tool_context, "build_bounded_digital_twin", toolbox.build_twin)


def simulate_interventions(tool_context: Any) -> dict[str, Any]:
    """Replay all bounded counterfactual intervention scenarios deterministically."""
    return _invoke_tool(tool_context, "simulate_interventions", toolbox.simulate)


def rank_and_verify_interventions(tool_context: Any) -> dict[str, Any]:
    """Apply mandatory gates, disqualify unsafe options, and verify the eligible winner."""
    return _invoke_tool(
        tool_context, "rank_and_verify_interventions", toolbox.rank_and_verify
    )


def prepare_human_decision_brief(tool_context: Any) -> dict[str, Any]:
    """Prepare evidence and impact for a human decision; never approve or execute it."""
    return _invoke_tool(tool_context, "prepare_human_decision_brief", toolbox.prepare_brief)


STRANDS_TOOLS = [
    _decorate(inspect_operational_state),
    _decorate(collect_operational_evidence),
    _decorate(forecast_bottleneck),
    _decorate(build_bounded_digital_twin),
    _decorate(simulate_interventions),
    _decorate(rank_and_verify_interventions),
    _decorate(prepare_human_decision_brief),
]

SYSTEM_PROMPT = """
You are Bottleneck IQ HumanGuard, an autonomous reliability agent for professional SRE teams.

Your authority is deliberately bounded:
- Use only the provided read-only or simulation tools.
- Treat persisted evidence, deterministic calculations, and mandatory gates as authoritative.
- Never invent telemetry, evidence, hashes, tool results, probabilities, or deployment outcomes.
- Never approve a recommendation or claim that production was changed.
- Never reveal hidden reasoning. Report concise evidence, tool results, and uncertainty.

For a new or partially completed workflow, inspect state and then use the remaining tools in this
order: collect evidence, forecast, build the Digital Twin, simulate, rank and verify, prepare the
human decision brief. Stop when the workflow reaches AWAITING_HUMAN. Your final answer must state
the predicted crossing, rejected unsafe option, verified recommendation, material uncertainty,
and the exact decision required from the human. Always end with: PRODUCTION ACTION: NOT EXECUTED.
""".strip()


def runtime_status() -> dict[str, Any]:
    return {
        "enabled": settings.strands_enabled,
        "sdk_available": STRANDS_AVAILABLE and find_spec("strands") is not None,
        "provider": "Amazon Bedrock",
        "model_id": settings.bedrock_model_id,
        "region": settings.aws_region,
        "agentcore_ready": find_spec("bedrock_agentcore") is not None,
        "background_monitor_enabled": settings.background_monitor_enabled,
        "production_action": "NOT_EXECUTED",
    }


def _audit(workflow_id: int, event_type: str, payload: dict[str, Any]) -> str:
    with SessionLocal() as db:
        run = workflow.require_run(db, workflow_id)
        workflow.append_event(db, run, event_type, "strands-orchestrator", payload)
        return run.state


def _offline_fallback(workflow_id: int, reason: str) -> StrandsRunResult:
    trace: list[str] = []
    calls = [
        ("inspect_operational_state", toolbox.inspect),
        ("collect_operational_evidence", toolbox.observe),
        ("forecast_bottleneck", toolbox.forecast),
        ("build_bounded_digital_twin", toolbox.build_twin),
        ("simulate_interventions", toolbox.simulate),
        ("rank_and_verify_interventions", toolbox.rank_and_verify),
        ("prepare_human_decision_brief", toolbox.prepare_brief),
    ]
    for name, action in calls:
        action(workflow_id)
        trace.append(name)
    state = _audit(
        workflow_id,
        "strands.fallback_completed",
        {"reason": reason[:240], "tool_trace": trace, "production_action": "NOT_EXECUTED"},
    )
    return StrandsRunResult(
        workflow_id=workflow_id,
        runtime="deterministic-offline-fallback",
        model_id=settings.bedrock_model_id,
        state=state,
        surfaced_to_human=state == "AWAITING_HUMAN",
        response=(
            "The bounded deterministic fallback completed the evidence, forecast, simulation, "
            "verification, and decision-brief workflow. Configure AWS credentials to demonstrate "
            "live Strands + Bedrock reasoning. PRODUCTION ACTION: NOT EXECUTED."
        ),
        tool_trace=trace,
    )


def invoke_workflow_agent(workflow_id: int, prompt: str) -> StrandsRunResult:
    _audit(
        workflow_id,
        "strands.invocation_started",
        {
            "model_id": settings.bedrock_model_id,
            "provider": "Amazon Bedrock",
            "production_action": "NOT_EXECUTED",
        },
    )
    if not settings.strands_enabled or not STRANDS_AVAILABLE:
        if settings.strands_offline_fallback:
            return _offline_fallback(workflow_id, "Strands SDK is disabled or unavailable")
        raise RuntimeError("Strands Agents SDK is disabled or unavailable")

    try:
        model_options: dict[str, Any] = {
            "model_id": settings.bedrock_model_id,
            "region_name": settings.aws_region,
            "temperature": 0.1,
            "max_tokens": 1800,
        }
        if settings.bedrock_guardrail_id:
            model_options.update(
                guardrail_id=settings.bedrock_guardrail_id,
                guardrail_version=settings.bedrock_guardrail_version,
                guardrail_trace="enabled",
            )
        model = BedrockModelClass(**model_options)
        agent = AgentClass(
            name="Bottleneck IQ HumanGuard",
            description="Autonomous, evidence-first reliability investigation with human approval.",
            system_prompt=SYSTEM_PROMPT,
            model=model,
            tools=STRANDS_TOOLS,
        )
        trace: list[str] = []
        result = agent(prompt, workflow_id=workflow_id, tool_trace=trace)
        with SessionLocal() as db:
            run = workflow.require_run(db, workflow_id)
            state = run.state
        _audit(
            workflow_id,
            "strands.invocation_completed",
            {"tool_trace": trace, "resulting_state": state, "production_action": "NOT_EXECUTED"},
        )
        return StrandsRunResult(
            workflow_id=workflow_id,
            runtime="strands-bedrock",
            model_id=settings.bedrock_model_id,
            state=state,
            surfaced_to_human=state == "AWAITING_HUMAN",
            response=str(result),
            tool_trace=trace,
        )
    except Exception as exc:
        _audit(
            workflow_id,
            "strands.invocation_failed",
            {"error_type": type(exc).__name__, "production_action": "NOT_EXECUTED"},
        )
        if settings.strands_offline_fallback:
            return _offline_fallback(workflow_id, type(exc).__name__)
        raise

