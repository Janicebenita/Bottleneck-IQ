# WCC submission draft

## Project name

Bottleneck IQ HumanGuard

## Tagline

A Strands-powered reliability agent that investigates tomorrow's incident today—and contacts an engineer only when a verified decision is ready.

## Submission category

Operational intelligence and AI-assisted reliability

## The problem

Site reliability engineers repeatedly correlate telemetry, topology, capacity,
failure modes, mitigation options, and business impact under severe time
pressure. Conventional alerts arrive after a threshold is crossed and still
leave the engineer with hours of investigative work.

## What it does

Bottleneck IQ HumanGuard runs quietly in the background. When operational risk
emerges, a Strands agent collects evidence, forecasts the capacity crossing,
builds a bounded Digital Twin, replays twelve counterfactual scenarios,
disqualifies unsafe mitigations, verifies the strongest eligible option, and
prepares a concise human decision brief. It never approves or changes
production. A qualified engineer is contacted only after deterministic safety
gates pass.

## How we built it

- Strands Agents SDK for autonomous tool selection and orchestration
- Amazon Bedrock for model reasoning
- Amazon Bedrock AgentCore-compatible runtime entrypoint
- FastAPI and Pydantic for typed APIs and contracts
- SQLAlchemy for workflow, evidence, execution, and audit persistence
- React and TypeScript for the decision workspace
- Deterministic forecasting, Digital Twin simulation, mandatory safety gates,
  SHA-256-linked audit events, and verifiable evidence export

## What makes it different

The model is useful but never authoritative. Strands decides how to investigate;
deterministic code decides whether evidence and mitigations pass. This produces
autonomy without surrendering operational control.

## Accomplishments

- Seven bounded Strands tools cover the investigation end to end.
- Every Strands invocation and tool result is persisted in the audit chain.
- Unsafe FAST mitigation is rejected even when it appears attractive.
- Background monitoring stays quiet until a verified human decision is needed.
- Offline fallback is explicitly labeled and never presented as live Bedrock evidence.

## Built with

Strands Agents SDK, Amazon Bedrock, Amazon Bedrock AgentCore, Python, FastAPI,
Pydantic, SQLAlchemy, React, TypeScript, Docker, OpenTelemetry, pytest, Vitest.

## Safety boundary

Bottleneck IQ is decision support: it gathers evidence, evaluates bounded
interventions, and prepares a recommendation, but it does not deploy or modify
production systems. A qualified human remains the final authority.
