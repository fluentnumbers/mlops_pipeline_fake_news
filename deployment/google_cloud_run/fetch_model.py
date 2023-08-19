import os

import mlflow
from dotenv import load_dotenv
from mlflow.tracking import MlflowClient

load_dotenv()


def fetch_model(MLFLOW_TRACKING_URI: str, model_name: str) -> None:
    """
    Download the artifacts of the latest production version of a model from MLflow.

    This function first creates an MLflow client with the provided tracking URI.
    Then, it retrieves the latest production version of the model.
    Finally, it downloads the artifacts of the model version to a local directory.
    """
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
    prod_version = client.get_latest_versions(name=model_name, stages=["Production"])[0]
    run_id = prod_version.run_id
    # artifact_path=MLFLOW_ARTIFACT_LOCATION not needed as mlflow knows it
    mlflow.artifacts.download_artifacts(run_id=run_id, dst_path="./artifact")


if __name__ == "__main__":
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")
    MODEL_NAME = os.getenv("MODEL_NAME")
    fetch_model(MLFLOW_TRACKING_URI, MODEL_NAME)
