# WCC Final Submission Checklist

Use this list in order. Do not claim a managed AWS service as live until you have captured evidence from your own account.

## Required before submission

- [ ] Push this converted project to the public GitHub repository.
- [ ] Confirm the repository About section displays the MIT license.
- [ ] Follow the root README from a clean checkout and fix any missing setup step.
- [ ] Configure AWS credentials and request access to the selected Amazon Bedrock model.
- [ ] Run a real Strands + Bedrock invocation and save the runtime status, request ID, timestamp, and screenshot.
- [ ] Confirm the Judge Demo visibly says `LIVE_BEDROCK`, not `OFFLINE_FALLBACK`, during the recorded demo.
- [ ] Deploy `deploy/agentcore/main.py` to Bedrock AgentCore Runtime if budget and account access allow.
- [ ] If deployed, record the AgentCore ARN, region, invocation output, and CloudWatch evidence.
- [ ] Deploy a stable public demo and verify it in an incognito browser.
- [ ] Add the public demo URL to the WCC submission.
- [ ] Export or screenshot the Mermaid architecture diagram.
- [ ] Record a demo video no longer than five minutes.
- [ ] Submit the public repository URL, video URL, description, and architecture diagram.

## Five-minute video proof

- [ ] State the problem, user, and why it matters in the first 30 seconds.
- [ ] Show the quiet monitor finding a workflow that needs attention.
- [ ] Show a live Strands run calling multiple named tools.
- [ ] Show the forecast, digital twin, candidate simulations, and safety gates.
- [ ] Show one concise human decision brief.
- [ ] Show that no infrastructure action is executed automatically.
- [ ] Show audit evidence and live AWS runtime status.
- [ ] End with measurable impact and the WCC category.

## WCC positioning

Project name: **Bottleneck IQ HumanGuard**

Category: **Operational intelligence and AI-assisted reliability**

One-line pitch: **A quiet Strands agent that predicts operational incidents, simulates safe interventions, and asks an operator only when a consequential decision is ready.**

Avoid unsupported claims such as “production deployed,” “AgentCore verified,” or “prevents every outage.” Prefer evidence-backed language: “deployment-ready,” “verified locally,” or “observed in this live run.”

## Supporting material

- [ ] Explain the Strands tool design, Bedrock integration, AgentCore architecture, and human-approval boundary.
- [ ] Link any supporting technical article in the WCC submission.

## Final quality gate

- [ ] No secrets, AWS keys, private URLs, or personal data are committed.
- [ ] Tests pass from a clean checkout.
- [ ] Every link in the README and WCC entry works.
- [ ] Audio is clear and on-screen text is readable at normal playback speed.
- [ ] The repository, video, and WCC description tell the same story.
- [ ] The submission is sent before the deadline; do not wait for the final minutes.
