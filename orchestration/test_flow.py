import os

from dotenv import load_dotenv
from prefect import flow
from prefect.deployments import Deployment
from prefect_gcp.cloud_run import CloudRunJob
from prefect_gcp.cloud_storage import GcsBucket

load_dotenv()

# PREFECT_BLOCKNAME_CLOUD_RUN_JOB = os.environ["PREFECT_BLOCKNAME_CLOUD_RUN_JOB"]
# PREFECT_BLOCKNAME_GCP_BUCKET = os.environ["PREFECT_BLOCKNAME_GCP_BUCKET"]
# gcs_bucket = GcsBucket.load(PREFECT_BLOCKNAME_GCP_BUCKET)
# cloud_run_job = CloudRunJob.load(PREFECT_BLOCKNAME_CLOUD_RUN_JOB)


@flow(log_prints=True)
def basic_prefect_flow():
    print("Hello, Prefect!")


if __name__ == "__main__":
    # basic_prefect_flow()
    """
    prefect deployment build orchestration/test_flow.py:basic_prefect_flow -n cloud-run-deployment -ib cloud-run-job/${PREFECT_BLOCKNAME_CLOUD_RUN_JOB} -sb gcs-bucket/${PREFECT_BLOCKNAME_GCP_BUCKET}
    """
    # Deploy the prefect workflow
    deployment = Deployment.build_from_flow(
        flow=basic_prefect_flow,
        name="main",
        version=1,
        work_queue_name="default",
        # infrastructure=cloud_run_job,
        # storage=gcs_bucket,
    )
    deployment.apply()
