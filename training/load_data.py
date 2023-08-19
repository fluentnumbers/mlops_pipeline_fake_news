import os
import zipfile
from pathlib import Path

import kaggle
from dotenv import load_dotenv
from prefect import flow, get_run_logger, task
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from prefect.task_runners import SequentialTaskRunner
from prefect_gcp.cloud_storage import GcsBucket

load_dotenv()

# KAGGLE_USERNAME = os.environ["KAGGLE_USERNAME"]
# KAGGLE_KEY = os.environ["KAGGLE_KEY"]

KAGGLE_DATASET_PATH = os.environ["KAGGLE_DATASET_PATH"]

PREFECT_BLOCKNAME_GCP_BUCKET = os.environ["PREFECT_BLOCKNAME_GCP_BUCKET"]

# GCP_BUCKETNAME = os.environ["GCP_BUCKETNAME"]

GLOVE_EMBEDDINGs_URL = "icw123/glove-twitter"

# subfolder where raw data is stored locally (temporary) to be uploaded to the GCP bucket subfolder with the same name
raw_data_subfolder = os.environ["GCP_RAW_DATA_SUBFOLDER"]
Path(raw_data_subfolder).mkdir(parents=True, exist_ok=True)


@task
def download_kaggle_dataset(KAGGLE_DATASET_PATH: str, raw_data_subfolder: Path):
    """
    Get dataset from Kaggle API
    """
    logger = get_run_logger()
    logger.info("Downloading Dataset")
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(KAGGLE_DATASET_PATH, path=f"{raw_data_subfolder}")


# @task
# def download_glove(GLOVE_EMBEDDINGs_URL: str, raw_data_subfolder:Path):
#     """
#     Get glove embeddings from Kaggle API: https://archive.li/APGfO
#     """
#     logger = get_run_logger()
#     logger.info("Downloading Glove embeddings")
#     kaggle.api.authenticate()
#     kaggle.api.dataset_download_file(
#         GLOVE_EMBEDDINGs_URL,
#         file_name="glove.twitter.27B.100d.txt",
#         path=f"{raw_data_subfolder}",
#     )


@task
def unzip(raw_data_subfolder: Path):
    logger = get_run_logger()
    logger.info("Unzipping...")
    dir_list = os.listdir(raw_data_subfolder)
    for file in dir_list:
        if file.endswith(".zip"):
            with zipfile.ZipFile(f"{raw_data_subfolder}/{file}", "r") as zip_ref:
                for file_unzipped in zip_ref.infolist():
                    if file_unzipped.filename not in dir_list:
                        logger.info(f"Unzipping... {file}")
                        zip_ref.extract(file_unzipped, raw_data_subfolder)


@task
def delete_zip(raw_data_subfolder: Path):
    logger = get_run_logger()
    logger.info("Deleting zip files")
    dir_list = os.listdir(raw_data_subfolder)
    for file in dir_list:
        if file.endswith(".zip"):
            logger.info(f"Deleting {file}")
            os.remove(Path(raw_data_subfolder).joinpath(file))


# Delete files within the directory
@task
def delete_files_inside_directory(directory_path: Path):
    print(Path(directory_path).absolute())
    for file_name in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)


@flow(name="load_kaggle_dataset")
def load_kaggle_dataset(kaggle_path: str, raw_data_subfolder: Path):
    logger = get_run_logger()
    logger.info(f"Downloading from {kaggle_path}")
    dataset = download_kaggle_dataset.submit(kaggle_path, raw_data_subfolder)
    unzipper = unzip.submit(raw_data_subfolder, wait_for=[dataset])
    delete_zip.submit(raw_data_subfolder, wait_for=[unzipper])


@flow(task_runner=SequentialTaskRunner())
def load_data(raw_data_subfolder: Path = raw_data_subfolder):
    logger = get_run_logger()
    Path(raw_data_subfolder).mkdir(parents=True, exist_ok=True)
    load_kaggle_dataset(KAGGLE_DATASET_PATH, raw_data_subfolder)
    load_kaggle_dataset(GLOVE_EMBEDDINGs_URL, raw_data_subfolder)
    gcs_bucket = GcsBucket.load(PREFECT_BLOCKNAME_GCP_BUCKET)
    gcs_bucket_path = raw_data_subfolder
    logger.info(
        f"Uploading from local {raw_data_subfolder} to GCP bucket {gcs_bucket.basepath}/{gcs_bucket_path}"
    )
    gcs_bucket.upload_from_folder(raw_data_subfolder, to_folder=gcs_bucket_path)
    delete_files_inside_directory(raw_data_subfolder)


if __name__ == "__main__":
    # load_data()

    # Deploy the prefect workflow
    deployment = Deployment.build_from_flow(
        flow=load_data,
        name="main",
        version=1,
        schedule=CronSchedule(
            cron="0 9 1 * *",  # Run the prefect flow at 09:00 (GMT-4), 21:00 (GMT+8) on every 1st day of month
            timezone="Europe/Amsterdam",
        ),
    )
    deployment.apply()
