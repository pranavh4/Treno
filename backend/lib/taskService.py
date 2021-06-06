from flask.globals import request
import tensorflow as tf
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
from tensorflow.keras.optimizers import SGD, Adam
from .task import Task, TaskSolution
import pandas as pd
import numpy as np
from pyunpack import Archive
from pathlib import Path
import requests
import wget
from .utils import bcolors, generateSignature, validateSignature
import traceback
from threading import get_ident
import json, os
from urllib.parse import urlparse

# Task:
#     |
#     |---data
#     |   |---train.csv
#     |   |---test.csv
#     |
#     |---model
#     |
#     |---config.json

thresholdReached = False

class EarlyStoppingByValAcc(tf.keras.callbacks.Callback):
    global thresholdReached
    def __init__(self, monitor='val_accuracy', value = 0.8):
        super(tf.keras.callbacks.Callback, self).__init__()
        self.monitor = monitor
        self.value = value

    def on_epoch_end(self, epoch, logs={}): 
        val_accuracy = logs.get(self.monitor)
        if(val_accuracy >= self.value): 
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Threshold acc reached, stopping training ...")
            self.model.stop_training = True
            thresholdReached = True


class TaskService:
    
    downloadFolder = None
    solutionFolder = None
    taskFolder = None
    taskSolutionFolder = None
    os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"
    
    credentialsPath = Path(__file__).parent / "../../kaggle.json"
    with credentialsPath.open() as f:
        credentials = json.load(f)
    print(credentials)
    os.environ["KAGGLE_USERNAME"] = credentials["username"]
    os.environ["KAGGLE_KEY"] = credentials["key"]
    # print(os.environ)

    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()

    @staticmethod
    def setFilePaths(port):
        TaskService.downloadFolder = Path(__file__).parent / f"../../mlFiles/{port}/downloads"
        TaskService.solutionFolder = Path(__file__).parent / f"../../mlFiles/{port}/solutions"
        TaskService.taskFolder = Path(__file__).parent / f"../../mlFiles/{port}/currentTask"
        TaskService.taskSolutionFolder =  Path(__file__).parent / f"../../mlFiles/{port}/taskSolution"

    @staticmethod
    def uploadTaskSolution(fileName: str):
        url = "https://transfer.sh/solution"

        payload = Path(TaskService.solutionFolder / "{fileName}.h5".format(fileName=fileName)).read_bytes()
        headers = {
            'Content-Type': 'application/octet-stream'
        }
        print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Uploading TaskSolution ...")
        response = requests.request("PUT", url, headers=headers, data=payload)
        print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} TaskSolution Uploaded ...")
        return response.text

    @staticmethod
    def downloadTask(task: Task) -> str:
        # Alternate using requests module
        # payload={}
        # headers = {}
        # response = requests.request("GET", task.resourceURL, headers=headers, data=payload)
        # Path(TaskService.downloadFolder +"/" + task.resourceURL.split('/')[-1]).write_bytes(response.content)

        Path(TaskService.downloadFolder / task.getHash()).mkdir(parents=True, exist_ok=True)
        Path(TaskService.taskFolder).mkdir(parents=True, exist_ok=True)
        relativeUrl = urlparse(task.resourceURL).path[1:]
        datasetName = relativeUrl.split('/')[1]
        fileLoc = TaskService.downloadFolder / f"{task.getHash()}/{datasetName}.zip"
        downloadPath = TaskService.downloadFolder / f"{task.getHash()}/"
        print("RELATIVE URL: " + relativeUrl)
        print("DOWNLOAD PATH: " + str(downloadPath))
        if Path(fileLoc).exists():
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Task {task.getHash()} Already Downloaded ...")
        else:
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Downloading Task {task.getHash()} ...")
            # try:
                # file = wget.download(task.resourceURL, out=str(fileLoc))
            TaskService.api.dataset_download_files(relativeUrl, path = str(downloadPath))
            # except Exception as e:
            #     print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} WGET ERROR")
            #     for i in range(10000):
            #         continue
            #     file = wget.download(task.resourceURL, out=str(fileLoc)) 
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Download completed ..., ", fileLoc)
        #unzip to taskFolder
        print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Extracting the file ...")
        Archive(fileLoc).extractall(TaskService.taskFolder)
        return fileLoc

    @staticmethod
    def downloadTaskSolution(taskSolution: TaskSolution) -> str:
        # Path(TaskService.downloadFolder + "/taskSolutions").mkdir(parents=True, exist_ok=True)
        Path(TaskService.taskSolutionFolder).mkdir(parents=True, exist_ok=True)
        fileLoc = TaskService.taskSolutionFolder / f"{taskSolution.getHash()}.h5"
        if Path(fileLoc).exists():
            Path(fileLoc).unlink()
        # else:
        print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Downloading TaskSolution of ID {taskSolution.taskId}...")
        try:
            file = wget.download(taskSolution.modelURL, out=str(fileLoc))
        except Exception as e:
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} WGET ERROR")
            for i in range(10000):
                continue
            file = wget.download(taskSolution.modelURL, out=str(fileLoc)) 

        print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Download completed of ID {taskSolution.taskId}...")

    @staticmethod
    def runTask(task: Task, publicKey: str, privateKey: str) -> TaskSolution:
        try:
            global thresholdReached 
            thresholdReached = False
            #read data
            train = pd.read_csv(TaskService.taskFolder / 'data/train.csv',  header=None)   
            test = pd.read_csv(TaskService.taskFolder / 'data/test.csv',  header=None)   
            
            #spliting x and y
            yTrain = train.iloc[: , -1]
            yTest = test.iloc[: , -1] 
            xTrain = train.drop(train.columns[-1],axis=1)
            xTest = test.drop(test.columns[-1],axis=1)
            
            #transforming y to categorical
            yTrainCat = to_categorical(yTrain)
            yTestCat = to_categorical(yTest)

            #load model
            mlModel = tf.keras.models.load_model(TaskService.taskFolder / 'model')
            physical_devices = tf.config.list_physical_devices('GPU')
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Device available : ", physical_devices)
            
            #create solutions folder if not present
            Path(TaskService.solutionFolder).mkdir(parents=True, exist_ok=True)

            #callbacks to save best acc mdodel, stop on reaching threshold
            checkpointer1 = ModelCheckpoint(
                filepath= TaskService.solutionFolder / '{id}.h5'.format(id=task.getHash()), 
                verbose=1, 
                save_best_only=True,
                save_weights_only=True, 
                monitor='val_accuracy'
            )
            checkpointer2 = EarlyStoppingByValAcc(
                 monitor='val_accuracy',
                 value=task.threshold / 100,
            )

            mlModel.compile(
                loss='categorical_crossentropy',
                optimizer=Adam(learning_rate=0.001),
                metrics=['accuracy']
            )

            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Starting to train task {task.getHash()}...")
            history = mlModel.fit(
                xTrain,
                yTrainCat,
                batch_size=32,
                epochs=task.maxEpochs,
                validation_data=(xTest, yTestCat),
                verbose=1,
                callbacks=[checkpointer1, checkpointer2]
            )
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} {bcolors.OKGREEN}{bcolors.BOLD}Completed training {task.getHash()}... {history.history} {bcolors.ENDC}")
            
            taskSolutionURL = TaskService.uploadTaskSolution(task.getHash())
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Task Solution URL: {taskSolutionURL}")
            taskSolution = TaskSolution(
                taskId = task.getHash(),
                modelURL = taskSolutionURL,
                accuracy = (history.history["val_accuracy"][-1] if thresholdReached else max(history.history["val_accuracy"])) * 100,
                wst = 2 if thresholdReached else 1,
                publicKey = publicKey,
                signature = ""
            )
            #sign the taskSolution
            taskSolution.signature = generateSignature(taskSolution.getUnsignedStr(),privateKey)
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} {taskSolution.toDict()}")
            return taskSolution
        except Exception as e:
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Error occured while training..\n", e.__repr__)
            traceback.print_exc()
  
    @staticmethod
    def __validateTaskFiles() -> bool:
        try:
            mlModel = tf.keras.models.load_model(TaskService.taskFolder / 'model')
            train = pd.read_csv(TaskService.taskFolder / 'data/train.csv',  header=None)   
            test = pd.read_csv(TaskService.taskFolder / 'data/test.csv',  header=None)   
            return True
        except Exception as e:
            print(e)
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Task File validation unsuccessful")
            return False  

    @staticmethod
    def validateTask(task: Task) -> bool:
        if not validateSignature(task.getUnsignedStr(), task.publicKey, task.signature):
            return False
        status = requests.get(url=task.resourceURL).status_code
        if status==404:
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} 404 Not Found Error")
            return False
        return True

    @staticmethod
    def validateTaskSolution(task: Task, taskSolution: TaskSolution) -> bool:
        print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Validating TaskSolution of ID {taskSolution.taskId}...")
        TaskService.validateTask(task)
        TaskService.downloadTask(task)
        TaskService.__validateTaskFiles()
        if taskSolution.taskId != task.getHash():
            return False
        if not validateSignature(taskSolution.getUnsignedStr(), taskSolution.publicKey, taskSolution.signature):
            return False
        TaskService.downloadTaskSolution(taskSolution)
        try:
            #read data
            test = pd.read_csv(TaskService.taskFolder / 'data/test.csv',  header=None)   
            
            #spliting x and y
            yTest = test.iloc[: , -1] 
            xTest = test.drop(test.columns[-1],axis=1)
            
            #transforming y to categorical
            yTestCat = to_categorical(yTest)

            #load model
            mlModel = tf.keras.models.load_model(TaskService.taskFolder / 'model')

            #load solution weights
            mlModel.load_weights(TaskService.taskSolutionFolder / f"{taskSolution.getHash()}.h5")
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Evaluating the model...")
            loss,acc = mlModel.evaluate(xTest,yTestCat)
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Model performance: loss: ",loss," acc: ", acc)

            if round(acc*100,2) != taskSolution.accuracy:
                return False
            elif  taskSolution.accuracy < task.threshold:
                if taskSolution.wst != 1:
                    return False
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Task Solution validation done successfully")
            return True

        except Exception as e:
            traceback.print_exc()
            return False

# if __name__ == "__main__":
#     taskk = Task("https://transfer.sh/1LGZpPT/poker.zip",70,10,"30819f300d06092a864886f70d010101050003818d0030818902818100cb8d1b8ae3f9e568284f181f3c5fc2cf98c2e13a9f21734fa41a33bed6745e93f95c6f44e27a5f9992981c3d1bd613166f8bbf9a2245f576deb91049354635887c62eeb22969ef63a7b5fc2c53701b067dcc9425e11dac183f3328c4b64dd6493b454b09b9d24e228acd8f8795ce673b4804549a4c9de6dca9511252bb5e97530203010001","")
#     taskk.signature = generateSignature(taskk.getUnsignedStr(),"3082025b02010002818100cb8d1b8ae3f9e568284f181f3c5fc2cf98c2e13a9f21734fa41a33bed6745e93f95c6f44e27a5f9992981c3d1bd613166f8bbf9a2245f576deb91049354635887c62eeb22969ef63a7b5fc2c53701b067dcc9425e11dac183f3328c4b64dd6493b454b09b9d24e228acd8f8795ce673b4804549a4c9de6dca9511252bb5e975302030100010281800b95c2658b4823c863d2ec9a8a8320c153fe737734ab60b6bdae4817aa79011106f63dd6fbd4df300c69dfe1927e02a41a4127ec8bdad377aa8179edd0bc683b7c491d7f26016600750725bcc2b3138ac3c84c8eb47fa59bc30c517ca212d6ba0d841ceb7baed795a9a007767a8d59faeb68c28367f82925593a2b6f04c23561024100cdd1a3829426ab3c8d765c996d44cc90140150cf9972f408025f70b3707d1e625c9e25fde646641752633f55d25379574f10cc3bf73ebb42b4d9c95b62867d39024100fd2dedb0a58f4f8e416574c0da602318fb5c0e02569ac9f2d157bb4bea4ba73b45740d53b6496409c3c2c658558ad0c58a9ca624c940e537c8d93f46ac5ac4eb024007d6b4238500f4049a5ea7a830412e894e39be9a297df74d56c9cbc109c7ba2084e6810bea7943d69f8ca81cdca5d1394209a1bda6ecfcb4cdae7dbcbd43e20102400ecdb8b0337e05b0d3b212f993cb3b4222b067414bbf113fd96dbfcdd88d43e1fb55a5d1d73ec352aed79cb15d8f1855f49ce43a126a70fcaa09c9e160028eb10240686c70c1cad0a791c41dfbc226c19436f9ccc18bab480bfbbc0322782dff73a2248acfedddaba4f1cf22fa8fa34815803e80b2e9b2f94f63695b0d8217d983e8")
#     print(TaskService.validateTask(taskk))
#     taskSol = TaskService.runTask(taskk,"30819f300d06092a864886f70d010101050003818d0030818902818100cb8d1b8ae3f9e568284f181f3c5fc2cf98c2e13a9f21734fa41a33bed6745e93f95c6f44e27a5f9992981c3d1bd613166f8bbf9a2245f576deb91049354635887c62eeb22969ef63a7b5fc2c53701b067dcc9425e11dac183f3328c4b64dd6493b454b09b9d24e228acd8f8795ce673b4804549a4c9de6dca9511252bb5e97530203010001","3082025b02010002818100cb8d1b8ae3f9e568284f181f3c5fc2cf98c2e13a9f21734fa41a33bed6745e93f95c6f44e27a5f9992981c3d1bd613166f8bbf9a2245f576deb91049354635887c62eeb22969ef63a7b5fc2c53701b067dcc9425e11dac183f3328c4b64dd6493b454b09b9d24e228acd8f8795ce673b4804549a4c9de6dca9511252bb5e975302030100010281800b95c2658b4823c863d2ec9a8a8320c153fe737734ab60b6bdae4817aa79011106f63dd6fbd4df300c69dfe1927e02a41a4127ec8bdad377aa8179edd0bc683b7c491d7f26016600750725bcc2b3138ac3c84c8eb47fa59bc30c517ca212d6ba0d841ceb7baed795a9a007767a8d59faeb68c28367f82925593a2b6f04c23561024100cdd1a3829426ab3c8d765c996d44cc90140150cf9972f408025f70b3707d1e625c9e25fde646641752633f55d25379574f10cc3bf73ebb42b4d9c95b62867d39024100fd2dedb0a58f4f8e416574c0da602318fb5c0e02569ac9f2d157bb4bea4ba73b45740d53b6496409c3c2c658558ad0c58a9ca624c940e537c8d93f46ac5ac4eb024007d6b4238500f4049a5ea7a830412e894e39be9a297df74d56c9cbc109c7ba2084e6810bea7943d69f8ca81cdca5d1394209a1bda6ecfcb4cdae7dbcbd43e20102400ecdb8b0337e05b0d3b212f993cb3b4222b067414bbf113fd96dbfcdd88d43e1fb55a5d1d73ec352aed79cb15d8f1855f49ce43a126a70fcaa09c9e160028eb10240686c70c1cad0a791c41dfbc226c19436f9ccc18bab480bfbbc0322782dff73a2248acfedddaba4f1cf22fa8fa34815803e80b2e9b2f94f63695b0d8217d983e8")
#     # taskSol = TaskSolution(taskk.getHash(),"https://transfer.sh/rW6/solution",57.08,1,"30819f300d06092a864886f70d010101050003818d0030818902818100cb8d1b8ae3f9e568284f181f3c5fc2cf98c2e13a9f21734fa41a33bed6745e93f95c6f44e27a5f9992981c3d1bd613166f8bbf9a2245f576deb91049354635887c62eeb22969ef63a7b5fc2c53701b067dcc9425e11dac183f3328c4b64dd6493b454b09b9d24e228acd8f8795ce673b4804549a4c9de6dca9511252bb5e97530203010001","441c635ce25cf44e477e2f8bb3d9f375cbfe1598a443368fa8d691de331acaa43bb9a65df40e603216cc7b313e3e8c70be6671ee63006a49850f7f207b96583b3c73edfd9bdc3b3d6c3c80b56433147e7169fec4e7c5a3dd931fce25033fcbbb20eecb1e07870363aa4c2425aa633e1a442fa9017f2a9b14162cc64cf12deb22")
#     print(TaskService.validateTaskSolution(taskk,taskSol))
