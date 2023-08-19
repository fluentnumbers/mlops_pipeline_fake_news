LOCAL_TAG:=$(shell date +"%Y-%m-%d-%H")
LOCAL_IMAGE_NAME:=${ECR_REPO_NAME}:${LOCAL_TAG}
SHELL := /bin/bash

include .env
export



.EXPORT_ALL_VARIABLES:



GOOGLE_APPLICATION_CREDENTIALS = ${GCP_CREDENTIALS_PATH}
REPO_DIR = ${PWD}

MLFLOW_TRACKING_URI = http://localhost:${MLFLOW_SERVER_PORT}
MLFLOW_ARTIFACT_LOCATION = gs://${GCP_BUCKETNAME}/${MLFLOW_ARTIFACT_SUBFOLDER}

# this is how environment variables can be passed to Terraform
# https://developer.hashicorp.com/terraform/cli/config/environment-variables
TF_VAR_project = ${GCP_PROJECT_ID}
TF_VAR_region = $(GCP_REGION)
TF_VAR_data_lake_bucket = $(GCP_BUCKETNAME)


gcp_auth:
	gcloud auth activate-service-account --key-file ${GOOGLE_APPLICATION_CREDENTIALS}


#############################################
################# INFRASTRUCTURE
##############################################

# make vm_install_docker
vm_install_docker:
	sudo apt-get install docker.io -y;\
	sudo groupadd docker;\
	sudo gpasswd -a ${USER} docker
	sudo service docker restart

# make vm_install_terraform
vm_install_terraform:
	cd /home/$(USER);\
	wget https://releases.hashicorp.com/terraform/1.5.4/terraform_1.5.4_linux_amd64.zip;\
	unzip -o terraform_1.5.4_linux_amd64.zip;\
	rm terraform_1.5.4_linux_amd64.zip;\
	sudo mv terraform /usr/local/bin/

# make vm_install_docker_compose
vm_install_docker_compose:
	sudo apt install docker docker-compose python3-pip make -y
	sudo chmod 666 /var/run/docker.sock


# make vm_install_conda
install_conda:
	source infrastructure/install_conda.sh

# make setup_venv
setup_venv:
	pip install -U pip
	pip install pipenv
	pipenv install --dev
	pipenv run pip install tf-nightly -q
	pre-commit install


# make trf_apply
trf_apply:
# echo ${TF_VAR_data_lake_bucket}
	cd infrastructure/terraform && \
	terraform init && \
	terraform plan && \
	terraform apply -auto-approve && \
	cd -

#############################################
################# TRACKING: MLFLOW
##############################################
mlflow_up:
	cd tracking/mlflow && docker-compose up && cd -

mlflow_down:
	cd tracking/mlflow && docker-compose down && cd -


#############################################
################# ORCHESTRATION: PREFECT
##############################################

pr_srv_up:
# start containers with prefect server (orion) and Postgres database
	cd orchestration/server && docker-compose up --build && cd -

pr_srv_down:
# stop Prefect server and database
	cd orchestration/server && docker-compose down && cd -

pr_ag_up:
# start Prefect agent locally
# cd orchestration/agent && docker-compose up --build && cd -
	prefect agent start --work-queue default

_draft_pr_ag_down:
# stop Prefect agent container
	orchestration/agent && docker-compose down && cd


# TODO: use GCP to host Prefect agent
# ISSUE: how to make 'local' docker container with Prefect server communicate to the agent on 'another' VM (or serverless)?
_draft_pr_agent_on_gcp_:
	gcloud artifacts repositories create test-example-repository --repository-format=docker --location=europe
	gcloud auth configure-docker europe-docker.pkg.dev
	docker build -t europe-docker.pkg.dev/${GCP_PROJECT_ID}/test-example-repository/prefect-gcp:2-python3.11 "config/prefect/gcp_cloud"
	docker push europe-docker.pkg.dev/${GCP_PROJECT_ID}/test-example-repository/prefect-gcp:2-python3.11
	gcloud services enable run.googleapis.com

pr_deploy:
# 1. create Prefect blocks (credential, storage, etc.)
# 2. Create deployments for load_data.py and train.py
	source orchestration/prefect_create_deployments.sh


load_data:
# Run load_data.py Prefect deployment
	prefect deployment run load-data/main

train_model:
# Run train.py Prefect deployment
	prefect deployment run train-model/main

train_model_fast:
# Run train.py Prefect deployment with custom arguments
	prefect deployment run train-model/main --param n_trials=1 --param n_epochs=1


#############################################
################# DEPLOYMENT
##############################################
# Deploy prediction service either locally or to Google Cloud Run API (managed serverless)

deploy_local_up:
# Deploy the best model for inference as a local web-service in a container
	cd deployment/web_service_local && docker-compose up && cd -

deploy_local_down:
# Stop deployment/web_service_local docker-compose
	cd deployment/web_service_local/ && docker-compose down && cd -

deploy_test_local:
# send a post request to check the service
	python deployment/web_service_local/test_web_service.py

deploy_to_gcp:
# envvar are not available inside docker build by default and gcloud build doesn't have --build-arg:
# https://til.simonwillison.net/cloudrun/using-build-args-with-cloud-run
	cd deployment/google_cloud_run && \
	gcloud services enable run.googleapis.com && \
	gcloud services enable cloudbuild.googleapis.com && \
	python fetch_model.py && \
	source deploy.sh && \
	cd -

deploy_test_gcp:
# send a post request to check the service
	python deployment/google_cloud_run/test_cloud_run.py

_deploy_to_gcp_build_container_locally_for_debug:
# envvar are not available inside docker build by default!!!
# test this deployment: curl -d '{"text":"sample text"}' -H "Content-Type: application/json" -X POST http://localhost:9697/classify
	cd deployment/google_cloud_run/ && \
	docker build . -t test_service --build-arg PORT=${DEPLOYMENT_WEB_SERVICE_GCP_PORT} && \
	docker run -p ${DEPLOYMENT_WEB_SERVICE_GCP_PORT}:${DEPLOYMENT_WEB_SERVICE_GCP_PORT} -it test_service && \
	cd -

_deploy_to_gcp_no_config:
# this will use the default ARG PORT=9697 as defined in Dockerfile
	cd deployment/google_cloud_run && \
	gcloud services enable run.googleapis.com && \
	gcloud services enable cloudbuild.googleapis.com && \
	python fetch_model.py && \
 	gcloud builds submit --tag gcr.io/${GCP_PROJECT_ID}/${GCP_PROJECT_ID}-endpoint && \
	gcloud run deploy ${GCP_PROJECT_ID}-endpoint --port ${DEPLOYMENT_WEB_SERVICE_GCP_PORT} \
	 --image gcr.io/${GCP_PROJECT_ID}/classify_endpoint --platform managed --region ${GCP_REGION} --allow-unauthenticated --max-instances 2 --memory 1G \
	cd -

testa:
	cd deployment/web_service_local/ && docker-compose config && cd -

#############################################
################# MONITORING
##############################################
_mnt_up:
	cd monitoring && docker-compose up && cd -

_mnt_down:
	cd monitoring && docker-compose down --remove-orphans && cd -

_mnt_report:
	cd monitoring && python batch_monitoring.py && cd -





#############################################
################# UTILITIES
##############################################
_test:
	@echo ${KAGGLE_KEY}

unit_tests:
	pytest tests/test_app.py --disable-warnings

# integration_test:

format_check:
	isort .
	black .
	pylint --recursive=y .


pre_commit:
	pre-commit run --all-files

docker_system_prune:
	docker system prune -f -a

docker_restart:
	sudo service docker restart

docker_remove_all:
	docker stop $$(docker ps -aq);\
	if [ -n "$$(docker ps -aq)" ]; then \
		docker rm $$(docker ps -aq); \
	else \
		echo "No containers found."; \
	fi
	if [ -n "$$(docker images -aq)" ]; then \
		docker rmi -f $$(docker images -aq); \
	else \
		echo "No images found."; \
	fi
	if [ -n "$$(docker images -aq)" ]; then \
		docker volume rm $(docker volume ls -q) \
	else \
		echo "No images found."; \
	fi
	docker volume prune --force
