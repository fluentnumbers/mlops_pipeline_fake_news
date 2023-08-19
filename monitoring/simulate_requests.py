import json
import os
from hashlib import sha1
from pathlib import Path
from time import sleep
from typing import Union

import pandas as pd
import requests
from dotenv import load_dotenv
from prefect import flow, get_run_logger, task
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from prefect_gcp.cloud_storage import GcsBucket

load_dotenv()

PREFECT_BLOCKNAME_GCP_BUCKET = os.environ["PREFECT_BLOCKNAME_GCP_BUCKET"]
gcs_bucket = GcsBucket.load(PREFECT_BLOCKNAME_GCP_BUCKET)

HOST = "127.0.0.1"
PORT = os.environ["DEPLOYMENT_WEB_SERVICE_LOCAL_PORT"]

# subfolder where raw data is stored on the GCP bucket
raw_data_subfolder = (
    f"./{os.environ['GCP_RAW_DATA_SUBFOLDER']}"  # NB: ./ needs to be prepended to the folder name
)
Path(raw_data_subfolder).mkdir(parents=True, exist_ok=True)


@task
def read_data(raw_data_subfolder: Union[Path, str]):
    raw_data_subfolder = Path(raw_data_subfolder)
    logger = get_run_logger()
    logger.info(f"Loading data from {raw_data_subfolder}...")

    # GCP ---> Local
    gcs_bucket.download_object_to_path(
        from_path=f"{raw_data_subfolder}/True.csv",
        to_path=f"{raw_data_subfolder}/True.csv",
    )
    gcs_bucket.download_object_to_path(
        from_path=f"{raw_data_subfolder}/Fake.csv",
        to_path=f"{raw_data_subfolder}/Fake.csv",
    )

    real_news = pd.read_csv(Path(raw_data_subfolder, "True.csv"))
    real_news["category"] = 1

    fake_news = pd.read_csv(Path(raw_data_subfolder, "Fake.csv"))
    fake_news["category"] = 0

    df = pd.concat([real_news, fake_news])
    df["text"] = df["title"] + "\n" + df["text"]
    df = df.drop(["title", "subject", "date"], axis=1)

    logger.info("Data loading successful!")

    df = df.sample(frac=1)
    return df


@flow()
def send_requests():
    def compute_hash(text):
        return sha1(text.lower().encode("utf-8")).hexdigest()

    data = read_data(raw_data_subfolder)
    endpoint_name = "classify"

    url = f"http://{HOST}:{PORT}/{endpoint_name}"

    with open("./monitoring/target.csv", "a", encoding="utf-8") as f_target:
        for index, row in data.iterrows():
            row["_id"] = compute_hash(row["text"])

            event = {"text": row["text"]}
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(event),
                timeout=600,
            ).json()

            pred = int(resp["class"] is True)
            f_target.write(f"{row['_id']},{row['category']},\n")
            print(f"class: {pred}")
            sleep(0.5)


if __name__ == "__main__":
    # send_data()

    # Deploy the prefect workflow
    deployment = Deployment.build_from_flow(
        flow=send_requests,
        name="main",
        version=1,
        work_queue_name="default",
        # storage=gcs_bucket,
        schedule=CronSchedule(
            cron="0 11 1 * *",  # Run the prefect flow at 11:00 (GMT-4), 21:00 (GMT+8) on every 1st day of month
            timezone="Europe/Amsterdam",
        ),
    )
    deployment.apply()
