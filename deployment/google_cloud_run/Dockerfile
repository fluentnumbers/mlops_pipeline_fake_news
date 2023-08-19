# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim
RUN apt-get update && apt-get install -qq -y curl
RUN pip install -U pip && pip install --upgrade pip

ARG PORT=9697
# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED=True
ENV PORT=$PORT
EXPOSE ${PORT}

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
COPY [ "./requirements.txt", "./" ]
RUN pip install -r requirements.txt >/dev/null

# Flask app
COPY [ "classify.py", "./" ]

# copy predownloaded artifacts, assuming fetch_model.py is run before image creation (see Makefile)
#TODO: make connection to hosted mlflow+storage and fetch the model from there
COPY ["./artifact", "."]

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind 0.0.0.0:${PORT}  --workers 1 --threads 8 --timeout 0 classify:app


# Use this instead for debugging and manually starting gunicorn from running container
# ENTRYPOINT [ "bash" ]
