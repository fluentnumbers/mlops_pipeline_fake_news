FROM python:3.10-slim
# FROM google/cloud-sdk:439.0.0
RUN apt-get update && apt-get install -qq -y curl
RUN pip install -U pip && pip install --upgrade pip
WORKDIR /app

COPY [ "./requirements.txt", "./" ]
RUN pip install -r requirements.txt >/dev/null
COPY [ "classify.py", "fetch_model.py", "./" ]

# Downloading gcloud package
RUN curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz > /tmp/google-cloud-sdk.tar.gz

# Installing the package
RUN mkdir -p /usr/local/gcloud \
  && tar -C /usr/local/gcloud -xvf /tmp/google-cloud-sdk.tar.gz > /dev/null \
  && /usr/local/gcloud/google-cloud-sdk/install.sh > /dev/null

# Adding the package path to local
ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin
