# pylint: disable=import-error
# pylint: disable=no-name-in-module

import os
import pickle
from hashlib import sha1
from pathlib import Path

import mlflow
import mlflow.pyfunc
import psycopg2
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from mlflow.tracking import MlflowClient
from tensorflow.keras.preprocessing import sequence

load_dotenv()

MONITORING_DATABASE_URI = os.environ["MONITORING_DATABASE_URI"]

app = Flask(__name__)


def prepare(text: str) -> sequence:
    def get_tokenizer() -> pickle:
        with open("./artifact/tokenizer.bin", "rb") as f_in:
            tokenizer = pickle.load(f_in)
        return tokenizer

    maxlen = 300
    tokenizer = get_tokenizer()
    tokens = tokenizer.texts_to_sequences([text])
    tokens_padded = sequence.pad_sequences(tokens, maxlen=maxlen)
    return tokens_padded


def classify(prepped_tokens: sequence) -> mlflow.models.Model:
    def load_model() -> mlflow.models.Model:
        uri_path = Path.cwd().joinpath(f"artifact/model").as_uri()
        model = mlflow.pyfunc.load_model(uri_path)
        return model

    print("Loading the model...")
    model = load_model()
    preds = model.predict(prepped_tokens)
    print("Prediction successfull!")
    return preds


def store_to_history(text: str, pred: int) -> int:
    def compute_hash(text):
        return sha1(text.lower().encode("utf-8")).hexdigest()

    CREATE_REQUESTS_HISTORY = (
        "CREATE TABLE IF NOT EXISTS history (id TEXT, text TEXT, prediction INT);"
    )
    INSERT_REQUEST_RETURN_ID = (
        "INSERT INTO history (id, text, prediction) VALUES (%s,%s,%s) RETURNING id;"
    )

    pg_conn = psycopg2.connect(MONITORING_DATABASE_URI)
    with pg_conn:
        with pg_conn.cursor() as cursor:
            cursor.execute(CREATE_REQUESTS_HISTORY)
            id = compute_hash(text)
            cursor.execute(INSERT_REQUEST_RETURN_ID, (id, text, pred))
            # id = cursor.fetchone()[0]
    return id


@app.route("/classify", methods=["POST"])
def classify_endpoint() -> jsonify:
    text = request.get_json()

    tokens = prepare(text["text"])
    pred = classify(tokens)
    int_pred = (pred > 0.5).astype("int32").tolist()[0][0]

    dict_map = {
        0: False,
        1: True,
    }

    final_pred = dict_map[int_pred]

    if MONITORING_DATABASE_URI != "":
        id = store_to_history(text["text"], int_pred)

    result = {
        "text": text["text"],
        "class": final_pred,
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=os.environ["DEPLOYMENT_WEB_SERVICE_LOCAL_PORT"])
