import json
import os

from dotenv import load_dotenv
from prefect.filesystems import GitHub
from prefect.infrastructure.container import DockerContainer
from prefect_gcp import CloudRunJob, GcpCredentials, GcsBucket
from prefect_gcp.cloud_storage import GcsBucket

load_dotenv()

GCP_CREDENTIALS_PATH = os.environ.get("GCP_CREDENTIALS_PATH")
GCP_BUCKETNAME = os.environ.get("GCP_BUCKETNAME")
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")

PREFECT_BLOCKNAME_GCP_CREDENTIALS = os.environ.get("PREFECT_BLOCKNAME_GCP_CREDENTIALS")
PREFECT_BLOCKNAME_GCP_BUCKET = os.environ.get("PREFECT_BLOCKNAME_GCP_BUCKET")
PREFECT_BLOCKNAME_DOCKER = os.environ.get("PREFECT_BLOCKNAME_DOCKER")
PREFECT_BLOCKNAME_GITHUB = os.environ.get("PREFECT_BLOCKNAME_GITHUB")
PREFECT_BLOCKNAME_CLOUD_RUN_JOB = os.environ["PREFECT_BLOCKNAME_CLOUD_RUN_JOB"]

GITHUB_REPO_PATH = os.environ.get("GITHUB_REPO_PATH")


with open(GCP_CREDENTIALS_PATH, "r") as creds:
    gcp_creds = json.load(creds)


#############################################
################# GCP Credentials
##############################################
credentials_block = GcpCredentials(
    service_account_info=gcp_creds  # enter your credentials from the json file
)
credentials_block.save(PREFECT_BLOCKNAME_GCP_CREDENTIALS, overwrite=True)
print(f"Created GCP credentials block named {PREFECT_BLOCKNAME_GCP_CREDENTIALS}")


#############################################
################# GCP storage bucket
##############################################
bucket_block = GcsBucket(
    gcp_credentials=GcpCredentials.load(PREFECT_BLOCKNAME_GCP_CREDENTIALS),
    bucket=f"{GCP_BUCKETNAME}",  # insert your  GCS bucket name
)

bucket_block.save(PREFECT_BLOCKNAME_GCP_BUCKET, overwrite=True)
print(f"Created GCP bucket block named {PREFECT_BLOCKNAME_GCP_BUCKET}")


#############################################
################# GCP Cloud Run
##############################################
# must be from GCR and have Python + Prefect
image = f"europe-docker.pkg.dev/{os.environ['GCP_PROJECT_ID']}/test-example-repository/prefect-gcp:2-python3.11"  # noqa

cloud_run_job = CloudRunJob(
    image=image,
    credentials=credentials_block,
    region=os.environ["GCP_REGION"],
)
cloud_run_job.save(PREFECT_BLOCKNAME_CLOUD_RUN_JOB, overwrite=True)
print(f"Created Github block named {PREFECT_BLOCKNAME_CLOUD_RUN_JOB}")


#############################################
################# GitHub
##############################################
gh_block = GitHub(name=PREFECT_BLOCKNAME_GITHUB, repository=GITHUB_REPO_PATH)
gh_block.save(PREFECT_BLOCKNAME_GITHUB, overwrite=True)
print(f"Created Github block named {PREFECT_BLOCKNAME_GITHUB}")
