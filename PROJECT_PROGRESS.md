<!-- vscode-markdown-toc -->
- [Zoomcamp criteria self-evaluation](#zoomcamp-criteria-self-evaluation)
- [Project progress](#project-progress)
	- [Infrastructure](#infrastructure)
			- [Cloud](#cloud)
			- [IaC](#iac)
	- [Data](#data)
	- [Training](#training)
			- [Experiment tracking](#experiment-tracking)
	- [Orchestration](#orchestration)
	- [Deployment](#deployment)
	- [Monitoring](#monitoring)
	- [Best practices](#best-practices)
			- [Unit-tests](#unit-tests)
			- [Integration tests](#integration-tests)
			- [Pre-commit hooks](#pre-commit-hooks)
					- [Formatting](#formatting)
			- [Makefile](#makefile)
			- [CI\\CD](#cicd)

<!-- vscode-markdown-toc-config
	numbering=false
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->


# Zoomcamp criteria self-evaluation
|  Criteria | Value  |
|---|---|
| Problem description  |   2 points: The problem is well described and it's clear what the problem the project solves|
| Cloud | 4 points: The project is developed on the cloud and IaC tools are used for provisioning the infrastructure |
|Experiment tracking and model registry   | 4 points: Both experiment tracking and model registry are used  |
| Workflow orchestration  | 4 points: Fully deployed workflow  |
| Model deployment   |  4 points: The model deployment code is containerized and could be deployed to cloud or special tools for model deployment are used  |
| Model monitoring  | 0/4 points: No model monitoring |
| Reproducibility  | 4 points: Instructions are clear, it's easy to run the code, and it works. The versions for all the dependencies are specified. |
| Best practices |--------------------------------------------------------------------------------------------------- |
| Unit-tests | 1 point|
| Integration test | 0/1 point |
|  Linter and/or code formatter are used | 1 point  |
| Makefile| 1 point|
| pre-commit hooks | 1 point |
| CI/CD pipeline | 0/2 point |
| Total | -----------------------------------------------------------------------------------------------------------------|
|        |   26/33 points

# Project progress

## <a name='Infrastructure'></a>[Infrastructure](./infrastructure/README.md)

#### <a name='Cloud'></a>Cloud
- [x] GCP cloud is used to load&read data, training artifacts, models
- [x] GCP Cloud run is used to host serverless prediction service
- [ ] ==TODO: use cloud APIs for managed services, such as databases, MLFlow, etc.==

#### <a name='IaC'></a>IaC
- [x] IaC using Terraform, currently only to [create a GCP bucket](./infrastructure/README.md#gcp-infrastructure-setup-with-terraform)
- [ ] ==TODO: Terraform usage can be expanded to automate creation of the GCP project, the VM itself and more==
  - [Terraform Deploy Prefect Server to GCP](https://gist.github.com/TylerWanner/0b4b00f4701dae6ad0a98978efe01966)

## <a name='Data'></a>Data
- [x] [Datasets](./README.md#datasets) automatically fetched from Kaggle
- [ ] ==TODO: Add another news dataset for real-time inference imitation and testing==
- [ ] ==TODO: Add DVC for data version control==

## [Training](./training/README.md)

- [x] hyperparameter tuning using hyperopts

#### [Experiment tracking](./tracking/README.md)
- [x] Dockerized MLflow with model registry on the cloud
  - [MLFlow on GCP for Experiment Tracking](https://kargarisaac.github.io/blog/mlops/data%20engineering/2022/06/15/MLFlow-on-GCP.html)
  - [MLOps project- part 1: Machine Learning Experiment Tracking Using MLflow](https://kargarisaac.github.io/blog/mlops/2022/08/09/machine-learning-experiment-tracking-mlflow.html)

## [Orchestration](./orchestration/README.md)
- [x] Prefect is used to orchestrate data loading and training processes
  - [Prefect - Docker Compose](https://github.com/flavienbwk/prefect-docker-compose/tree/main#run-the-server)
- [x] Containerized Prefect server run
- [ ] ==TODO: Containerize Prefect agent to run them independently on another VM and get triggered==
  - [Long-running containers with Workflows and Compute Engine](https://cloud.google.com/blog/topics/developers-practitioners/long-running-containers-workflows-and-compute-engine)
  - [Long running job with Cloud Workflows](https://medium.com/google-cloud/long-running-job-with-cloud-workflows-38b57bea74a5)
- [ ] ==TODO: Run Prefect in using Cloud Run==
  - [Serverless Prefect Flows with Google Cloud](https://medium.com/the-prefect-blog/serverless-prefect-flows-with-google-cloud-run-jobs-23edbf371175)
- [ ] ==TODO: Trigger flows by data changes using DVC==

## [Deployment](./deployment/README.md)
- [x] Option to deploy as a local web service (Flask)
- [x] Option to deploy as a GCP Cloud Run serverless function
  - [Adapted from here](https://github.com/patrickloeber/ml-deployment/tree/main/google-cloud-run)
  - [gcloud run deploy  |  Google Cloud CLI Documentation](https://cloud.google.com/sdk/gcloud/reference/run/deploy)
  - [MLOps project - part 3: Machine Learning Model Deployment](https://kargarisaac.github.io/blog/mlops/2022/08/28/machine-learning-model-deployment.html#Machine-Learning-Model-Deployment)
  - [ ] ==TODO: Make connection btw Cloud Run and MLflow\GCP to fetch the best model in the run-time (currently at the moment of deploy)==
- [ ] ==TODO: FastAPI==
- [ ] ==TODO: online streaming?==


## [Monitoring](./monitoring/README.MD)
  - [x] Local web service has [history database](./deployment/README.md#storing-incoming-requests) attached
    - [Build your first REST API with Flask and PostgreSQL](https://blog.teclado.com/first-rest-api-flask-postgresql-python/)
  - [ ] ==TODO: Implement monitoring for managed endpoint==
    - [ ] ==TODO: host the monitoring services (evidently AI, Prometheus, Grafana, PostGres) on GCP Cloud through Terraform==
  - [ ] ==TODO: Comprehensive model monitoring that sends alerts or runs a conditional workflow (e.g. retraining, generating debugging dashboard, switching to a different model) if the defined metrics threshold is violated==





  - [MLOps project - part 4a: Machine Learning Model Monitoring](https://kargarisaac.github.io/blog/mlops/2022/09/05/machine-learning-model-monitoring.html)
  - Evidently

## [Best practices](./best%20practices/README.md)

#### Unit-tests
- [x] [unit-tests](./best%20practices/README.md#unit_tests) are added
- [ ] ==TODO: increase unit-tests coverage==


#### Integration tests
- [ ] ==TODO:==

#### Pre-commit hooks
- [x] [pre-commit hooks](./.pre-commit-config.yaml) is installed and setup

###### Formatting
- [x] [pylint and Black](./best%20practices/README.md) are used

#### Makefile
- [x] [Makefile](./Makefile) is used in this project

#### CI\CD
- [ ] ==TODO:==
