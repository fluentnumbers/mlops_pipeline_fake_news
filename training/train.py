#!/usr/bin/python

# pylint: disable=import-error
# pylint: disable=no-name-in-module
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals

import argparse
import os
import pickle
import re
import string
from datetime import datetime
from pathlib import Path
from typing import Tuple, Union

import mlflow
import nltk
import numpy as np
import optuna
import pandas as pd
import tensorflow as tf
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from keras.callbacks import LearningRateScheduler, ReduceLROnPlateau
from keras.layers import LSTM, Dense, Embedding
from keras.models import Sequential
from keras.optimizers.schedules import ExponentialDecay
from keras.preprocessing import sequence, text
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient
from nltk.corpus import stopwords
from optuna.integration import TFKerasPruningCallback

# from tensorflow import keras
from pandas import DataFrame
from prefect import flow, get_run_logger, task
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from prefect.task_runners import SequentialTaskRunner
from prefect_gcp.cloud_storage import GcsBucket
from sklearn.model_selection import train_test_split

load_dotenv()

PREFECT_BLOCKNAME_GCP_BUCKET = os.environ["PREFECT_BLOCKNAME_GCP_BUCKET"]
gcs_bucket = GcsBucket.load(PREFECT_BLOCKNAME_GCP_BUCKET)

raw_data_subfolder = (
    f"./{os.environ['GCP_RAW_DATA_SUBFOLDER']}"  # NB: ./ needs to be prepended to the folder name
)
EMBEDDING_FILE = f"{raw_data_subfolder}/glove.twitter.27B.100d.txt"

# Get environment variables needed for the experiment
MLFLOW_TRACKING_URI = os.environ["MLFLOW_TRACKING_URI"]
MLFLOW_ARTIFACT_LOCATION = os.environ["MLFLOW_ARTIFACT_LOCATION"]
MODEL_NAME = os.environ["MODEL_NAME"]


@task
def read_data(raw_data_subfolder: Union[str, Path]) -> DataFrame:
    """
    Load, preprocess, and merge real and fake news data.
    """
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
    return df


def denoise_text(text: str) -> str:
    """Removes HTML tags, square brackets, and stopwords."""

    def strip_html(text: str) -> str:
        """Removes HTML tags from the text."""
        return BeautifulSoup(text, "html.parser").get_text()

    def remove_between_square_brackets(text: str) -> str:
        """Removes content within square brackets in the text."""
        return re.sub("\[[^]]*\]", "", text)

    def remove_stopwords(text: str) -> str:
        """Removes English stopwords and punctuation from the text."""
        stop = set(stopwords.words("english")).union(set(string.punctuation))
        return " ".join(word.strip() for word in text.split() if word.strip().lower() not in stop)

    return remove_stopwords(remove_between_square_brackets(strip_html(text)))


@task
def clean_split_data(
    df: pd.DataFrame,
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Applies denoising and splits the data into training and test sets."""
    logger = get_run_logger()
    logger.info("Cleaning and Splitting the Data")

    df["text"] = df["text"].apply(denoise_text)

    x_train, x_test, y_train, y_test = train_test_split(df.text, df.category, random_state=0)

    logger.info("Done")

    return x_train, x_test, y_train, y_test


@task
def tokenize(
    x_train: pd.Series, x_test: pd.Series, max_features: int, maxlen: int
) -> Tuple[np.ndarray, np.ndarray, text.Tokenizer]:
    """Tokenizes text data and pads sequences to a maximum length."""

    logger = get_run_logger()
    logger.info("Tokenizing...")

    tokenizer = text.Tokenizer(num_words=max_features)
    tokenizer.fit_on_texts(x_train)

    x_train_tokenized = tokenizer.texts_to_sequences(x_train)
    x_train_padded = sequence.pad_sequences(x_train_tokenized, maxlen=maxlen)

    x_test_tokenized = tokenizer.texts_to_sequences(x_test)
    x_test_padded = sequence.pad_sequences(x_test_tokenized, maxlen=maxlen)

    logger.info("Tokenizing...done")

    return x_train_padded, x_test_padded, tokenizer


@task
def get_glove_embedding(
    EMBEDDING_FILE: str, tokenizer: text.Tokenizer, max_features: int
) -> np.ndarray:
    """Creates an embedding matrix from the GloVe embeddings."""

    def get_coefs(word: str, *arr: str) -> Tuple[str, np.ndarray]:
        return word, np.asarray(arr, dtype="float32")

    logger = get_run_logger()
    logger.info("Creating glove embedding matrix...")

    # GCP --> Local
    gcs_bucket.download_object_to_path(from_path=f"{EMBEDDING_FILE}", to_path=f"{EMBEDDING_FILE}")

    with open(EMBEDDING_FILE, "r", encoding="utf8") as f_out:
        embeddings_index = dict(get_coefs(*o.rstrip().rsplit(" ")) for o in f_out)

    all_embs = np.stack(embeddings_index.values())
    emb_mean, emb_std = all_embs.mean(), all_embs.std()
    embed_size = all_embs.shape[1]
    word_index = tokenizer.word_index
    nb_words = min(max_features, len(word_index))

    embedding_matrix = np.random.normal(emb_mean, emb_std, (nb_words, embed_size))

    for word, i in word_index.items():
        if i >= max_features:
            continue
        embedding_vector = embeddings_index.get(word)
        if embedding_vector is not None:
            embedding_matrix[i] = embedding_vector

    logger.info("Creating glove embedding matrix...Done")

    return embedding_matrix


def create_lstm_model(trial, max_features, embed_size, embedding_matrix, maxlen):
    model = Sequential()
    model.add(
        Embedding(
            max_features,
            output_dim=embed_size,
            weights=[embedding_matrix],
            input_length=maxlen,
            trainable=False,
        )
    )
    dropout_rate_1 = trial.suggest_float("lstm_dropout", 0.0, 0.3)
    mlflow.log_param(
        "dropout_lstm_layer_1",
        dropout_rate_1,
    )
    model.add(
        LSTM(
            units=128,
            return_sequences=True,
            recurrent_dropout=dropout_rate_1,
            dropout=dropout_rate_1,
        )
    )
    dropout_rate_2 = trial.suggest_float("lstm_dropout_2", 0.0, 0.2)
    mlflow.log_param("dropout_lstm_layer_2", dropout_rate_2)
    model.add(LSTM(units=64, recurrent_dropout=dropout_rate_2, dropout=dropout_rate_2))
    activation_1 = trial.suggest_categorical("activation", ["relu", "selu", "elu"])
    mlflow.log_param("activation_1", activation_1)
    model.add(Dense(units=32, activation=activation_1))
    model.add(Dense(1, activation="sigmoid"))
    # lr = trial.suggest_uniform("lr", 1e-5, 1e-1)
    # mlflow.log_param("learning_rate", lr)
    mlflow.log_artifact("./tokenizer.bin")
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    return model


@task
def train(
    x_train: pd.Series,
    y_train: pd.Series,
    batch_size: int,
    x_test: pd.Series,
    y_test: pd.Series,
    epochs: int,
    max_features: int,
    embed_size: int,
    embedding_matrix: np.ndarray,
    maxlen: int,
    n_trials: int,
) -> optuna.study.Study:
    """Trains an LSTM model with hyperparameters optimized by Optuna."""

    def objective(
        trial,
        x_train,
        y_train,
        batch_size,
        x_test,
        y_test,
        epochs,
        max_features,
        embed_size,
        embedding_matrix,
        maxlen,
    ):
        tf.keras.backend.clear_session()
        with mlflow.start_run():
            model = create_lstm_model(trial, max_features, embed_size, embedding_matrix, maxlen)

            model.fit(
                x_train,
                y_train,
                batch_size=batch_size,
                validation_data=(x_test, y_test),
                epochs=epochs,
                callbacks=[TFKerasPruningCallback(trial, "val_loss")],
            )

            scheduler = ExponentialDecay(1e-3, 400 * ((len(x_train) * 0.8) / batch_size), 1e-5)
            lr = LearningRateScheduler(scheduler, verbose=0)

            score = model.evaluate(x_test, y_test, verbose=0)
            mlflow.log_metric("accuracy", score[1])

        return score[1]

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(),
        pruner=optuna.pruners.HyperbandPruner(),
    )

    study.optimize(
        lambda trial: objective(
            trial,
            x_train,
            y_train,
            batch_size,
            x_test,
            y_test,
            epochs,
            max_features,
            embed_size,
            embedding_matrix,
            maxlen,
        ),
        show_progress_bar=True,
        n_trials=n_trials,
    )

    return study


@task
def register_best_model(experiment_name, MLFLOW_TRACKING_URI, MODEL_NAME):
    # pylint: disable=too-many-statements
    logger = get_run_logger()
    logger.info("Checking run and Registering best model to Production")
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
    experiment = client.get_experiment_by_name(experiment_name)

    # Get best run from current experiment
    runs = client.search_runs(
        experiment_ids=experiment.experiment_id,
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=1,
        order_by=["metrics.val_accuracy DESC"],
    )

    # Get run id of best run
    cur_run_id = runs[0].info.run_id

    # Get latest registered model versions
    try:
        client.get_latest_versions(name=MODEL_NAME)
    except mlflow.exceptions.RestException:
        client.create_registered_model(MODEL_NAME)  # create registered model if not exist

    # Check if model currently in production
    if (
        len(client.get_latest_versions(name=MODEL_NAME, stages=["Production"])) != 0
    ):  # if yes, compare run val_accuracy to model val_accuracy
        prod_ver = client.get_latest_versions(name=MODEL_NAME, stages=["Production"])[0]
        prod_run_id = prod_ver.run_id
        prod_acc = client.get_metric_history(prod_run_id, "val_accuracy")[0].value
        run_acc = client.get_metric_history(cur_run_id, "val_accuracy")[0].value
        if (
            run_acc > prod_acc
        ):  # if run better than production model, register new model and move to production
            logger.info("Registering new model to Production ...")
            mlflow.register_model(model_uri=f"runs:/{cur_run_id}/model", name=MODEL_NAME)
            client.transition_model_version_stage(
                name=MODEL_NAME,
                version=client.get_latest_versions(name=MODEL_NAME, stages=["None"])[0].version,
                stage="Production",
                archive_existing_versions=False,
            )
            logger.info(
                "Moving previous model to Staging ..."
            )  # move previous prod model to staging
            client.transition_model_version_stage(
                name=MODEL_NAME,
                version=prod_ver.version,
                stage="Staging",
                archive_existing_versions=False,
            )
        # else if production better than run, check if model in staging
        elif (
            len(client.get_latest_versions(name=MODEL_NAME, stages=["Staging"])) != 0
        ):  # if yes, compare run val_accuracy to model val_accuracy
            stag_ver = client.get_latest_versions(name=MODEL_NAME, stages=["Staging"])[0]
            stag_run_id = stag_ver.run_id
            stag_acc = client.get_metric_history(stag_run_id, "val_accuracy")[0].value
            if (
                run_acc > stag_acc
            ):  # if run better than staging model, register new model and move to staging
                logger.info("Registering new model to Staging ...")
                mlflow.register_model(model_uri=f"runs:/{cur_run_id}/model", name=MODEL_NAME)
                client.transition_model_version_stage(
                    name=MODEL_NAME,
                    version=client.get_latest_versions(name=MODEL_NAME, stages=["None"])[0].version,
                    stage="Staging",
                    archive_existing_versions=False,
                )
                client.transition_model_version_stage(  # remove previous model from staging
                    name=MODEL_NAME,
                    version=stag_ver.version,
                    stage="None",
                    archive_existing_versions=False,
                )
        else:  # if models in production and staging are both better, do nothing
            logger.info("Models in Production are better.")

    elif (
        len(client.get_latest_versions(name=MODEL_NAME, stages=["Production"])) == 0
        and len(client.get_latest_versions(name=MODEL_NAME, stages=["Staging"])) != 0
    ):  # run if model not in production but in staging
        stag_ver = client.get_latest_versions(name=MODEL_NAME, stages=["Staging"])[0]
        stag_run_id = stag_ver.run_id
        stag_acc = client.get_metric_history(stag_run_id, "val_accuracy")[0].value
        run_acc = client.get_metric_history(cur_run_id, "val_accuracy")[0].value
        if (
            run_acc > stag_acc
        ):  # if run better than staging model, register new model and move to production
            logger.info("Registering model to Production ...")
            mlflow.register_model(model_uri=f"runs:/{cur_run_id}/model", name=MODEL_NAME)
            client.transition_model_version_stage(
                name=MODEL_NAME,
                version=client.get_latest_versions(name=MODEL_NAME, stages=["None"])[0].version,
                stage="Production",
                archive_existing_versions=False,
            )
        else:  # promote model in staging to production if better than run
            logger.info(
                "Promoting previous model to Production and Registering new model to Staging ..."
            )
            mlflow.register_model(model_uri=f"runs:/{cur_run_id}/model", name=MODEL_NAME)
            client.transition_model_version_stage(
                name=MODEL_NAME,
                version=client.get_latest_versions(name=MODEL_NAME, stages=["Staging"])[0].version,
                stage="Production",
                archive_existing_versions=False,
            )
            client.transition_model_version_stage(  # register new run to staging
                name=MODEL_NAME,
                version=client.get_latest_versions(name=MODEL_NAME, stages=["None"])[0].version,
                stage="Staging",
                archive_existing_versions=False,
            )
    else:  # if no models in production and staging
        logger.info("Registering new model to Production ...")  # register run to production
        mlflow.register_model(model_uri=f"runs:/{cur_run_id}/model", name=MODEL_NAME)
        client.transition_model_version_stage(
            name=MODEL_NAME,
            version=client.get_latest_versions(name=MODEL_NAME, stages=["None"])[0].version,
            stage="Production",
            archive_existing_versions=False,
        )


# Decorator to define a flow of execution named "train model"
@flow()
def train_model(n_trials: int = 2, n_epochs: int = 2):
    # Get a logger for this run
    logger = get_run_logger()
    logger.info(f"Start training...")
    logger.info(f"No of optimization trials = {n_trials}")
    logger.info(f"Training for {n_epochs} epochs")

    # Download NLTK's stopword corpus
    nltk.download("stopwords")

    # Get current time, format it, and append it to experiment name
    timer = datetime.now()
    timer = timer.strftime("%Y-%m-%d-%H-%M")
    experiment_name = f"train.py-{timer}"

    # Set the mlflow tracking URI and create an experiment
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.create_experiment(experiment_name, artifact_location=MLFLOW_ARTIFACT_LOCATION)
    mlflow.set_experiment(experiment_name)
    mlflow.tensorflow.autolog()

    # Log the model name to which models will be registered
    logger.info(f"Models will be registered to {MODEL_NAME}")

    # Set some model parameters
    batch_size = 256
    embed_size = 100
    max_features = 10000
    maxlen = 300

    # Read the data and split it into training and test sets
    dataframe_future = read_data.submit(raw_data_subfolder)
    split_future = clean_split_data.submit(dataframe_future)
    x_train, x_test, y_train, y_test = split_future.result()

    # Tokenize the data
    tokenizer_future = tokenize.submit(
        x_train, x_test, max_features, maxlen, wait_for=[split_future]
    )
    x_train, x_test, tokenizer = tokenizer_future.result()

    # Save the tokenizer to log it later as an artifact
    with open("./tokenizer.bin", "wb") as f_out:
        pickle.dump(tokenizer, f_out)
    logger.info("Successfully saved the Tokenizer")

    # Generate an embedding matrix using the GloVe embeddings
    embedding_matrix_future = get_glove_embedding.submit(EMBEDDING_FILE, tokenizer, max_features)
    embedding_matrix = embedding_matrix_future.result()

    # Train the model
    train_future = train.submit(
        x_train,
        y_train,
        batch_size,
        x_test,
        y_test,
        n_epochs,
        max_features,
        embed_size,
        embedding_matrix,
        maxlen,
        n_trials,
        wait_for=[tokenizer_future, embedding_matrix_future],
    )

    # Register the best model from the experiment
    register_best_model.submit(
        experiment_name, MLFLOW_TRACKING_URI, MODEL_NAME, wait_for=[train_future]
    )


if __name__ == "__main__":
    # train_model()

    # Deploy the prefect workflow
    deployment = Deployment.build_from_flow(
        flow=train_model,
        name="main",
        version=1,
        work_queue_name="default",
        # storage=gcs_bucket,
        schedule=CronSchedule(
            cron="0 10 1 * *",  # Run the prefect flow at 10:00 (GMT-4), 21:00 (GMT+8) on every 1st day of month
            timezone="Europe/Amsterdam",
        ),
    )
    deployment.apply()
