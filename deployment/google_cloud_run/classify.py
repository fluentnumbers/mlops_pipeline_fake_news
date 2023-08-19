# pylint: disable=import-error
# pylint: disable=no-name-in-module

import os
import pickle
from pathlib import Path

import mlflow
import mlflow.pyfunc
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from mlflow.tracking import MlflowClient
from tensorflow.keras.preprocessing import sequence

load_dotenv()

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
        uri_path = Path.cwd().joinpath("artifact/model").as_uri()
        model = mlflow.pyfunc.load_model(uri_path)
        return model

    print("Loading the model...")
    model = load_model()
    preds = model.predict(prepped_tokens)
    print("Prediction successfull!")
    return preds


@app.route("/classify", methods=["POST"])
def classify_endpoint():
    text = request.get_json()

    tokens = prepare(text["text"])
    pred = classify(tokens)
    int_pred = (pred > 0.5).astype("int32").tolist()[0][0]

    dict_map = {
        0: False,
        1: True,
    }

    final_pred = dict_map[int_pred]

    result = {
        "text": text["text"],
        "class": final_pred,
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
    )
