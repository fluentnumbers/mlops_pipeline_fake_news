import requests
from dotenv import load_dotenv

load_dotenv()
import os

sample_text = "sample text"
endpoint_name = "classify"
PORT = os.environ["DEPLOYMENT_WEB_SERVICE_LOCAL_PORT"]


url = f"http://127.0.0.1:{PORT}/{endpoint_name}"
response = requests.post(url, json=dict(text=sample_text), timeout=300)
# print(response.text)
print(response.json())
