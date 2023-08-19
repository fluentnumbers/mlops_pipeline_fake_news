import mlflow
from dotenv import load_dotenv

load_dotenv()
import os

mlflow.set_tracking_uri(
    f"http://localhost:{os.environ['MLFLOW_SERVER_PORT']}"
)  # Replace with your MLflow server endpoint
# Start an MLflow run
with mlflow.start_run():
    # Create a dummy file
    dummy_data = "This is a dummy artifact."
    with open("dummy.txt", "w") as f:
        f.write(dummy_data)

    # Log the dummy file as an artifact
    mlflow.log_artifact("dummy.txt")

    # Optional: Log additional metrics, parameters, etc.
    mlflow.log_param("param1", 123)
    mlflow.log_metric("metric1", 0.89)
