#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-bottleneck-iq-wcc}"
REGION="${REGION:-asia-south1}"
REVISION="${REVISION:-$(git rev-parse HEAD)}"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/bottleneck-iq"
[[ "$PROJECT_ID" == "bottleneck-iq-wcc" ]] || { echo "Unexpected project" >&2; exit 2; }

for secret in bottleneck-iq-integration-token bottleneck-iq-role-token-secret bottleneck-iq-intern-access-code bottleneck-iq-senior-access-code; do
  gcloud secrets versions access latest --secret "$secret" --project "$PROJECT_ID" >/dev/null
done

deploy_private() {
  local service="$1" image="$2" account="$3" secret_args="${4:-}" image_revision="${5:-$REVISION}"
  local extra=()
  if [[ -n "$secret_args" ]]; then extra=(--set-secrets "$secret_args"); fi
  gcloud run deploy "$service" --project "$PROJECT_ID" --region "$REGION" --platform managed \
    --image "${REGISTRY}/${image}:${image_revision}" --service-account "${account}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --no-allow-unauthenticated --port 8080 --cpu 1 --memory 512Mi --concurrency 20 --timeout 60 \
    --min-instances 0 --max-instances 5 --set-env-vars PRODUCTION_EXECUTION=false,ENVIRONMENT=production \
    "${extra[@]}"
}

deploy_private bottleneck-iq-orchestrator orchestrator bottleneck-iq-orchestrator-sa
deploy_private bottleneck-iq-forecast-service forecast bottleneck-iq-forecast-sa
deploy_private bottleneck-iq-simulation-service simulator bottleneck-iq-simulation-sa
deploy_private bottleneck-iq-verification-service verification bottleneck-iq-verification-sa
deploy_private bottleneck-iq-evidence-service evidence bottleneck-iq-evidence-sa
deploy_private bottleneck-iq-gemma-service gemma bottleneck-iq-gemma-sa
deploy_private bottleneck-iq-mcp-server mcp bottleneck-iq-mcp-sa "INTEGRATION_TOKEN=bottleneck-iq-integration-token:latest,ROLE_TOKEN_SECRET=bottleneck-iq-role-token-secret:latest" "${MCP_REVISION:-$REVISION}"

API_SA="bottleneck-iq-api-gateway-sa@${PROJECT_ID}.iam.gserviceaccount.com"
ORCHESTRATOR_SA="bottleneck-iq-orchestrator-sa@${PROJECT_ID}.iam.gserviceaccount.com"
for service in bottleneck-iq-forecast-service bottleneck-iq-simulation-service bottleneck-iq-verification-service bottleneck-iq-evidence-service bottleneck-iq-gemma-service bottleneck-iq-mcp-server; do
  gcloud run services add-iam-policy-binding "$service" --project "$PROJECT_ID" --region "$REGION" --member "serviceAccount:${API_SA}" --role roles/run.invoker >/dev/null
  gcloud run services add-iam-policy-binding "$service" --project "$PROJECT_ID" --region "$REGION" --member "serviceAccount:${ORCHESTRATOR_SA}" --role roles/run.invoker >/dev/null
done

gcloud run deploy bottleneck-iq-api-gateway --project "$PROJECT_ID" --region "$REGION" --platform managed \
  --image "${REGISTRY}/api:${API_REVISION:-$REVISION}" --service-account "$API_SA" --allow-unauthenticated \
  --port 8080 --cpu 1 --memory 512Mi --concurrency 40 --timeout 60 --min-instances 0 --max-instances 1 \
  --set-env-vars PRODUCTION_EXECUTION=false,ENVIRONMENT=production,DEMO_APP_URL=,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION},BIGQUERY_DATASET=bottleneck_iq,PUBSUB_TOPIC=bottleneck-iq-workflow-events \
  --set-secrets INTEGRATION_TOKEN=bottleneck-iq-integration-token:latest,ROLE_TOKEN_SECRET=bottleneck-iq-role-token-secret:latest,INTERN_ACCESS_CODE=bottleneck-iq-intern-access-code:latest,SENIOR_ACCESS_CODE=bottleneck-iq-senior-access-code:latest

API_URL="$(gcloud run services describe bottleneck-iq-api-gateway --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
[[ "$API_URL" == https://* ]] || { echo "API gateway URL unavailable" >&2; exit 6; }

gcloud run deploy bottleneck-iq-frontend --project "$PROJECT_ID" --region "$REGION" --platform managed \
  --image "${REGISTRY}/frontend:${REVISION}" --service-account "bottleneck-iq-frontend-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --allow-unauthenticated --port 8080 --cpu 1 --memory 256Mi --concurrency 80 --timeout 60 --min-instances 0 --max-instances 5 \
  --set-env-vars "API_BASE_URL=${API_URL}"

FRONTEND_URL="$(gcloud run services describe bottleneck-iq-frontend --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
[[ "$FRONTEND_URL" == https://* ]] || { echo "Frontend URL unavailable" >&2; exit 7; }
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
[[ "$PROJECT_NUMBER" =~ ^[0-9]+$ ]] || { echo "Project number unavailable" >&2; exit 8; }
REGIONAL_FRONTEND_URL="https://bottleneck-iq-frontend-${PROJECT_NUMBER}.${REGION}.run.app"
CORS_ORIGINS="${FRONTEND_URL},${REGIONAL_FRONTEND_URL}"
gcloud run services update bottleneck-iq-api-gateway --project "$PROJECT_ID" --region "$REGION" \
  --update-env-vars "^|^CORS_ORIGINS=${CORS_ORIGINS}" >/dev/null

echo "FRONTEND_URL=${FRONTEND_URL}"
echo "REGIONAL_FRONTEND_URL=${REGIONAL_FRONTEND_URL}"
echo "API_URL=${API_URL}"
echo "Cloud Run deployment submitted for revision ${REVISION}. Run scripts/smoke_cloud_run.py before recording success."
