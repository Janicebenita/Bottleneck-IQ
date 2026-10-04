$ErrorActionPreference = 'Stop'
$ProjectId = if ($env:PROJECT_ID) { $env:PROJECT_ID } else { 'bottleneck-iq-wcc' }
$Region = if ($env:REGION) { $env:REGION } else { 'asia-south1' }
if ($ProjectId -ne 'bottleneck-iq-wcc') { throw "Unexpected project: $ProjectId" }
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) { throw 'gcloud is required' }
gcloud auth list --filter=status:ACTIVE --format='table(account,status)'
gcloud config get-value project
gcloud artifacts repositories describe bottleneck-iq --location $Region --format='value(name)'
gcloud run services list --region $Region --platform managed --format='table(metadata.name,status.url,status.latestReadyRevisionName)'
gcloud pubsub topics list --filter='name:bottleneck-iq-' --format='value(name)'
bq --project_id=$ProjectId show bottleneck_iq
Write-Output 'Verification enumerated configuration only; service health requires scripts/smoke_cloud_run.py.'
