# Five-minute demo script

## 0:00–0:30 — Problem and audience

“SREs lose hours correlating fragmented signals after an alert fires. Bottleneck IQ
HumanGuard investigates before impact and contacts a human only when a verified
decision is ready.”

## 0:30–1:00 — Quiet background trigger

Show a healthy dashboard. Start the seeded telemetry stream. Do not click through
manual workflow stages. Show the background monitor detecting the forecast risk
and starting the Strands invocation.

## 1:00–2:00 — Genuine Strands execution

Open the audit/timeline view. Show `strands.invocation_started` followed by the
bounded tool calls: evidence, forecast, Digital Twin, simulation, verification,
and decision brief. Briefly show `backend/app/strands_runtime/agent.py` and the
`@tool` definitions.

## 2:00–3:10 — Counterfactual evidence

Show the +30 minute capacity crossing and the twelve deterministic simulations.
Compare FAST, SAFE, and OPTIMAL. Emphasize that FAST is disqualified by a
mandatory failover gate even if its score is attractive.

## 3:10–4:00 — Human-only decision

Show the workflow stop at `AWAITING_HUMAN`. Display the concise recommendation,
contradictory evidence, uncertainty, and estimated impact. Demonstrate that the
Intern role cannot approve and that a Senior Developer must provide a rationale.

## 4:00–4:35 — Audit and evidence

Show the SHA-256-linked audit timeline and evidence package. State clearly that
approval records a governed decision and enables export; it does not deploy or
change infrastructure.

## 4:35–5:00 — AWS architecture and close

Show Strands + Bedrock + AgentCore architecture and a successful authenticated
AgentCore status/invocation only if actually deployed.

Close with: “Before an SRE receives an alert, Bottleneck IQ has already investigated
the bottleneck, tested the options, and prepared one verified decision. Production
action remains with the human.”
