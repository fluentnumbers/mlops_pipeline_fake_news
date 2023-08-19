import subprocess

import requests
from dotenv import load_dotenv

load_dotenv()
import os

"""
A script to send a POST request to a deployed model service.
- retrieve the endpoint URL of the deployed model service by its name ${GCP_PROJECT_ID}-endpoint
- construct the server link
- send a POST request to it
"""

sample_text = "sample text"
endpoint_name = "classify"
PORT = os.environ["DEPLOYMENT_WEB_SERVICE_GCP_PORT"]

command = """
curl \
  -s "https://${GCP_REGION}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/${GCP_PROJECT_ID}/services/${GCP_PROJECT_ID}-endpoint" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" | jq -r '.status.url'
"""
result = subprocess.run(command, shell=True, executable="/bin/bash", capture_output=True, text=True)
ENDPOINT_URL = result.stdout.strip()
print(f"ENDPOINT_URL: {ENDPOINT_URL}")

LOCAL_RUN = False  # for debugging IF the container is deployed locally, not to Google run
if LOCAL_RUN:  # NB: HTTPS endpoint when referring to GCP and HTTP when it is localhost !!!!
    server_link = f"http://localhost:{PORT}/{endpoint_name}"
else:
    server_link = f"{ENDPOINT_URL}/{endpoint_name}"

response = requests.post(
    server_link,
    timeout=5,
    json={"text": sample_text},
)
print(response.json())


"""
Command line one-liners
export ENDPOINT_URL=$(curl -s "https://${GCP_REGION}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/${GCP_PROJECT_ID}/services/${GCP_PROJECT_ID}-endpoint" -H "Authorization: Bearer $(gcloud auth print-access-token)" | jq -r '.status.url')
curl -d '{"text":"sample text"}' -H "Content-Type: application/json" -X POST ${ENDPOINT_URL}/classify
curl -d '{"text":"sample text"}' -H "Content-Type: application/json" -X POST http://localhost:${DEPLOYMENT_WEB_SERVICE_GCP_PORT}/classify -v
"""
