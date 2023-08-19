import os
import tempfile
from pathlib import Path

import kaggle
from dotenv import load_dotenv
from prefect import flow
from pytest import fail

from training.load_data import delete_files_inside_directory, load_kaggle_dataset

load_dotenv()


KAGGLE_DATASET_PATH = os.environ["KAGGLE_DATASET_PATH"]


def test_load_kaggle_dataset():
    """Test that connection to kaggle works"""
    KAGGLE_DATASET_PATH = os.environ["KAGGLE_DATASET_PATH"]

    try:

        @flow
        def test_flow():
            load_kaggle_dataset.fn(KAGGLE_DATASET_PATH, Path("data"))

        test_flow()
    except Exception as ME:
        fail(f"download_kaggle_dataset() raised {ME} unexpectedly!")


def test_delete_files_inside_directory():
    """Test a utility method"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        delete_files_inside_directory.fn(Path(tmpdirname))
        assert (
            len(os.listdir(tmpdirname)) == 0
        ), f"delete_files_inside_directory does not work as expected"
