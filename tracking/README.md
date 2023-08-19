![mlflow](https://img.shields.io/badge/mlflow-%23d9ead3.svg?style=for-the-badge&logo=numpy&logoColor=blue)
<!-- vscode-markdown-toc -->
* [Start MLflow](#StartMLflow)

<!-- vscode-markdown-toc-config
	numbering=false
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->

# <a name='ExperimentTracking'></a>Experiment Tracking

## <a name='StartMLflow'></a>Start MLflow
Experiment tracking, registering metrics and artifacts (models) is done using [containerized](./mlflow/docker-compose.yaml) MLFlow and MYSSQL servers.
Experiments' meta-info and metrics stored in the MYSQL database, but model registry location defined by the `${MLFLOW_ARTIFACT_LOCATION}` and should be pointing to the GCP [bucket created](../infrastructure/README.md#gcp-infrastructure-setup-with-terraform) like `gs://bucket_fakenews01/mlflow`.

Launch your Mlflow Tracking server with `make mlflow_up` (`make mlflow_down` to stop).

```bash
mlflow_up:
	cd tracking/mlflow && docker-compose up && cd -
```


[Previous: Orchestration](../orchestration/README.md) | [Next: Training](../training/README.md)
