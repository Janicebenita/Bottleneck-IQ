#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-bottleneck-iq-wcc}"
REGION="${REGION:-asia-south1}"
REPOSITORY="${REPOSITORY:-bottleneck-iq}"

[[ "$PROJECT_ID" == "bottleneck-iq-wcc" ]] || { echo "Refusing unexpected project: $PROJECT_ID" >&2; exit 2; }
command -v gcloud >/dev/null || { echo "gcloud is required" >&2; exit 3; }
ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -n1)"
[[ -n "$ACCOUNT" ]] || { echo "No active gcloud account" >&2; exit 4; }
gcloud billing projects describe "$PROJECT_ID" --format='value(billingEnabled)' | grep -qi true || { echo "Billing is not enabled" >&2; exit 5; }
gcloud config set project "$PROJECT_ID" >/dev/null

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com bigquery.googleapis.com pubsub.googleapis.com logging.googleapis.com monitoring.googleapis.com cloudtrace.googleapis.com aiplatform.googleapis.com serviceusage.googleapis.com
gcloud artifacts repositories describe "$REPOSITORY" --location "$REGION" >/dev/null 2>&1 || gcloud artifacts repositories create "$REPOSITORY" --repository-format=docker --location="$REGION" --description="Bottleneck IQ service images"

for name in frontend api-gateway orchestrator forecast simulation verification evidence gemma mcp ci-deployer; do
  email="bottleneck-iq-${name}-sa@${PROJECT_ID}.iam.gserviceaccount.com"
  gcloud iam service-accounts describe "$email" >/dev/null 2>&1 || gcloud iam service-accounts create "bottleneck-iq-${name}-sa" --display-name="Bottleneck IQ ${name}"
done

export GOOGLE_CLOUD_PROJECT="$PROJECT_ID" GOOGLE_CLOUD_REGION="$REGION" BIGQUERY_DATASET="bottleneck_iq"
python scripts/provision_bigquery.py
python scripts/provision_pubsub.py
for secret in JWT_SIGNING_SECRET DEMO_ROLE_CODE_HASHES bottleneck-iq-integration-token bottleneck-iq-role-token-secret bottleneck-iq-intern-access-code bottleneck-iq-senior-access-code; do
  gcloud secrets describe "$secret" --project "$PROJECT_ID" >/dev/null 2>&1 || gcloud secrets create "$secret" --project "$PROJECT_ID" --replication-policy=automatic >/dev/null
done
API_SA="bottleneck-iq-api-gateway-sa@${PROJECT_ID}.iam.gserviceaccount.com"
MCP_SA="bottleneck-iq-mcp-sa@${PROJECT_ID}.iam.gserviceaccount.com"
for secret in bottleneck-iq-integration-token bottleneck-iq-role-token-secret bottleneck-iq-intern-access-code bottleneck-iq-senior-access-code; do
  gcloud secrets add-iam-policy-binding "$secret" --project "$PROJECT_ID" \
    --member "serviceAccount:${API_SA}" --role roles/secretmanager.secretAccessor >/dev/null
done
for secret in bottleneck-iq-integration-token bottleneck-iq-role-token-secret; do
  gcloud secrets add-iam-policy-binding "$secret" --project "$PROJECT_ID" \
    --member "serviceAccount:${MCP_SA}" --role roles/secretmanager.secretAccessor >/dev/null
done
echo "Provisioning boundary complete for project=$PROJECT_ID region=$REGION account=$ACCOUNT"
echo "Secret containers exist, but no secret values were created or printed. Add versions before deployment."
