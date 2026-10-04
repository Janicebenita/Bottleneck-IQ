#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="${PROJECT_ID:-bottleneck-iq-wcc}"
REGION="${REGION:-asia-south1}"
[[ "$PROJECT_ID" == "bottleneck-iq-wcc" ]] || { echo "Unexpected project" >&2; exit 2; }
command -v gcloud >/dev/null || { echo "gcloud is required" >&2; exit 3; }
gcloud auth list --filter=status:ACTIVE --format='table(account,status)'
gcloud config get-value project
gcloud artifacts repositories describe bottleneck-iq --location "$REGION" --format='value(name)'
gcloud run services list --region "$REGION" --platform managed --format='table(metadata.name,status.url,status.latestReadyRevisionName)'
gcloud pubsub topics list --filter='name:bottleneck-iq-' --format='value(name)'
bq --project_id="$PROJECT_ID" show bottleneck_iq
echo "Verification enumerated configuration only; service health requires scripts/smoke_cloud_run.py."
