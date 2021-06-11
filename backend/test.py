import json

import os
from pathlib import Path



credentialsPath = Path(__file__).parent / "../kaggle.json"
with credentialsPath.open() as f:
    credentials = json.load(f)
print(credentials)
os.environ["KAGGLE_USERNAME"] = credentials["username"]
os.environ["KAGGLE_KEY"] = credentials["key"]
# print(os.environ)

from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()

# api.dataset_initialize("D:\\Pranav\\Coding\\Final_Year_Project\\model_test\\pokerdataset\\")
# api.dataset_initialize("D:\\Pranav\\Coding\\Final_Year_Project\\model_test\\breastcancer\\")

# api.dataset_create_new("D:\\Pranav\\Coding\\Final_Year_Project\\model_test\\pokerdataset\\", public= True, dir_mode='zip')
api.dataset_create_new("D:\\Pranav\\Coding\\Final_Year_Project\\model_test\\breastcancer\\", public= True, dir_mode='zip')