# AgentCore Runtime deployment

`main.py` implements the Amazon Bedrock AgentCore Runtime contract with
`BedrockAgentCoreApp`, including `POST /invocations` and the managed health
endpoint. It invokes the same Strands tools and deterministic safety gates used
by the FastAPI product.

## Prerequisites

- AWS account and credentials
- Python 3.10+
- Node.js 20+
- Amazon Bedrock model access in `AWS_REGION`
- AgentCore CLI: `npm install -g @aws/agentcore`

## Create the deployment project

From a clean parent directory, create the official Strands/Bedrock scaffold:

```bash
agentcore create \
  --project-name Bottleneck IQHumanGuard \
  --name Bottleneck IQHumanGuard \
  --language Python \
  --framework Strands \
  --model-provider Bedrock \
  --memory none \
  --build CodeZip
```

Copy this repository into the generated project, make
`deploy/agentcore/main.py` the generated agent entrypoint, and add the packages
from `requirements.txt` to its generated `pyproject.toml`.

## Verify before creating resources

```bash
agentcore dev --no-browser
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Investigate the latest workflow and stop at human review."}'
agentcore deploy --dry-run
```

Deploy and invoke only from an approved AWS account:

```bash
agentcore deploy
agentcore invoke --prompt "Investigate the latest workflow and stop at human review."
agentcore status
```

Do not describe AgentCore as deployed until `agentcore status` and a live
invocation succeed. Deployment creates AWS resources and can incur charges.
