# AWS Strands architecture

## Authority model

```mermaid
flowchart LR
    CW[CloudWatch / seeded telemetry] --> BM[Background Monitor]
    BM --> SA[Strands HumanGuard Agent]
    SA --> BR[Amazon Bedrock]
    SA --> T1[Evidence Tool]
    SA --> T2[Forecast Tool]
    SA --> T3[Digital Twin Tool]
    SA --> T4[Simulation Tool]
    SA --> T5[Verification Tool]
    SA --> T6[Decision Brief Tool]
    T1 & T2 & T3 & T4 & T5 & T6 --> DE[Deterministic Engine]
    DE --> DB[(Audit + Evidence Store)]
    SA -->|only after verification| H[Human SRE Decision]
    H --> EP[Evidence Package]
    SA -. hosted by .-> AC[Amazon Bedrock AgentCore Runtime]

    classDef human fill:#073b4c,color:#fff,stroke:#22d3ee
    class H human
```

The Strands model decides which bounded investigative tools to call. The model
does not calculate authoritative operational values. Forecasting, scenario
replay, candidate eligibility, mandatory gates, workflow transitions, role
authorization, and audit hashing remain deterministic backend responsibilities.

No Strands or AgentCore tool can deploy, scale, roll back, execute shell
commands, approve a recommendation, or mutate production infrastructure.

## Background behavior

When `BACKGROUND_MONITOR_ENABLED=true`, an application-lifespan task examines
the newest actionable workflow at the configured interval. It stays quiet when
there is no new work or a decision is already pending. A completed investigation
ends in `AWAITING_HUMAN` and is visible through the existing UI and audit stream.

## AWS services

- **Strands Agents SDK:** autonomous planning and bounded tool selection.
- **Amazon Bedrock:** managed model inference and optional Guardrails.
- **Amazon Bedrock AgentCore Runtime:** production hosting contract and deployment path.
- **CloudWatch/OTel:** AgentCore observability target after authenticated deployment.
- **IAM:** runtime identity and least-privilege Bedrock invocation.

AgentCore and CloudWatch are documented as deployment targets until an
authenticated deployment and trace have been captured. The local deterministic
fallback is visibly labeled and is never represented as a live Strands run.
