#!/bin/bash

: '
This script deploys a Docker image to Google Cloud Run.

It first checks if the necessary environment variable DEPLOYMENT_WEB_SERVICE_GCP_PORT is set.
Then, it defines the name of the Cloud Run service and the Docker image.
It creates a temporary Cloud Build config file and submits a Cloud Build job to build and push the Docker image.
Finally, it deploys the Docker image to Cloud Run with specified settings like region, max instances, memory, and port.

Arguments:
  None

Environment variables used:
  DEPLOYMENT_WEB_SERVICE_GCP_PORT: The port to be exposed by the Cloud Run service
  GCP_PROJECT_ID: The Google Cloud Project ID
  GCP_REGION: The region where the Cloud Run service is to be deployed
'

if [[ -z "$DEPLOYMENT_WEB_SERVICE_GCP_PORT" ]]; then
    echo "Must provide DEPLOYMENT_WEB_SERVICE_GCP_PORT environment variable" 1>&2
    exit 1
fi

NAME="${GCP_PROJECT_ID}-endpoint"  # main function in the module with the Flask app
IMAGE="gcr.io/${GCP_PROJECT_ID}/$NAME"

# Need YAML so we can set --build-arg
echo "
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '--tag', '$IMAGE', '.', '--build-arg', 'PORT=${DEPLOYMENT_WEB_SERVICE_GCP_PORT}']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '$IMAGE']
" > /tmp/cloudbuild.yml

gcloud builds submit --config /tmp/cloudbuild.yml

# rm /tmp/cloudbuild.yml

gcloud run deploy $NAME \
  --allow-unauthenticated \
  --platform=managed \
  --image $IMAGE \
  --region ${GCP_REGION} \
  --max-instances 2 \
  --memory 1G \
  --port ${DEPLOYMENT_WEB_SERVICE_GCP_PORT}
