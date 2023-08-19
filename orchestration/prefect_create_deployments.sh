
echo --------------------------- Create Prefect blocks -----------------------------------------------
python ./orchestration/create_blocks.py

echo --------------------------- Create Prefect deployment for /training/load_data.py ---------------------
python ./training/load_data.py
echo ------ One can run \"prefect deployment run load-data/main\" to load raw data

echo --------------------------- Create Prefect deployment for /training/train.py --------------------------
python ./training/train.py
echo ----- One can run \"prefect deployment run train-model/main\" to train and register the best model

echo --------------------------- Create Prefect deployment for /monitoring/simulate_requests.py --------------------------
python ./monitoring/simulate_requests.py
echo ----- One can run \"prefect deployment run send-requests/main\" to simulate sending requests to a local web server


# echo --------------------------- Run deployment load_data/main ---------------------------------------------
# prefect deployment run load_data/main
# echo --------------------------- Run deployment train_model/main ---------------------------------------------
# prefect deployment run train_model/main
