import tensorflow as tf
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
from tensorflow.keras.optimizers import SGD, Adam
from task import Task, TaskSolution
import pandas as pd
import numpy as np
from pyunpack import Archive
from pathlib import Path
import requests
import wget
from utils import generateSignature
import traceback

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
            print("Threshold acc reached, stopping training ...")
            self.model.stop_training = True
            thresholdReached = True


class TaskService:
    
    downloadFolder = "../../downloads"
    solutionFolder = "../../solutions"
    taskFolder = "../../currentTask"

    @staticmethod
    def uploadTaskSolution():
        url = "https://transfer.sh/solution"

        payload = Path(TaskService.solutionFolder + "/solution.h5").read_bytes()
        headers = {
            'Content-Type': 'application/octet-stream'
        }
        print("Uploading TaskSolution ...")
        response = requests.request("PUT", url, headers=headers, data=payload)
        print("TaskSolution Uploaded ...")
        return response.text

    @staticmethod
    def downloadTask(task: Task) -> str:
        # Alternate using requests module
        # payload={}
        # headers = {}
        # response = requests.request("GET", task.resourceURL, headers=headers, data=payload)
        # Path(TaskService.downloadFolder +"/" + task.resourceURL.split('/')[-1]).write_bytes(response.content)

        Path(TaskService.downloadFolder).mkdir(parents=True, exist_ok=True)
        Path(TaskService.taskFolder).mkdir(parents=True, exist_ok=True)
        print("Downloading Task ...")
        file = wget.download(task.resourceURL, out=TaskService.downloadFolder +"/" + task.resourceURL.split('/')[-1])
        print("Download completed ...")
        #unzip to taskFolder
        print("Extracting the file ...")
        Archive(file).extractall(TaskService.taskFolder)
        return file

    @staticmethod
    def runTask(task: Task, privateKey: str) -> TaskSolution:
        try:
            global thresholdReached 
            thresholdReached = False
            #read data
            train = pd.read_csv('../../currentTask/data/train.csv',  header=None)   
            test = pd.read_csv('../../currentTask/data/test.csv',  header=None)   
            
            #spliting x and y
            yTrain = train.iloc[: , -1]
            yTest = test.iloc[: , -1] 
            xTrain = train.drop(train.columns[-1],axis=1)
            xTest = test.drop(test.columns[-1],axis=1)
            
            #transforming y to categorical
            yTrainCat = to_categorical(yTrain)
            yTestCat = to_categorical(yTest)

            #load model
            mlModel = tf.keras.models.load_model(TaskService.taskFolder+'/model')
            physical_devices = tf.config.list_physical_devices('GPU')
            print("Device available : ", physical_devices)
            
            #create solutions folder if not present
            Path(TaskService.solutionFolder).mkdir(parents=True, exist_ok=True)

            #callbacks to save best acc mdodel, stop on reaching threshold
            checkpointer1 = ModelCheckpoint(
                filepath= TaskService.solutionFolder + '/solution.h5', 
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

            print("Starting to train...")
            history = mlModel.fit(
                xTrain,
                yTrainCat,
                batch_size=32,
                epochs=10,
                validation_data=(xTest, yTestCat),
                verbose=1,
                callbacks=[checkpointer1, checkpointer2]
            )
            print("Completed training...", history.history)
            
            taskSolutionURL = TaskService.uploadTaskSolution()
            print(taskSolutionURL)
            taskSolution = TaskSolution(
                task,
                taskSolutionURL,
                history.history["val_accuracy"][-1],
                1 if thresholdReached else 0.1,
                ""
            )
            #sign the taskSolution
            taskSolution.signature = generateSignature(taskSolution.getUnsignedStr(),privateKey)
            print(taskSolution.toDict())
            return taskSolution
        except Exception as e:
            print("Error occured while training..\n", e.__repr__)
            traceback.print_exc()
  
    @staticmethod
    def __verifyTaskFiles() -> bool:
        try:
            mlModel = tf.keras.models.load_model(TaskService.taskFolder+'/model')
            train = pd.read_csv('../../currentTask/data/train.csv',  header=None)   
            test = pd.read_csv('../../currentTask/data/test.csv',  header=None)   
            return True
        except:
            print("File verification unsuccessful")
            return False  

    @staticmethod
    def verifyTask(task: Task) -> bool:
        TaskService.downloadTask(task)
        TaskService.__verifyTaskFiles()

if __name__ == "__main__":
    taskk = Task("https://transfer.sh/1dfkQCG/poker.zip",51,10,"","")
    TaskService.downloadTask(taskk)
    xx = TaskService.runTask(taskk,"3082025b02010002818100cb8d1b8ae3f9e568284f181f3c5fc2cf98c2e13a9f21734fa41a33bed6745e93f95c6f44e27a5f9992981c3d1bd613166f8bbf9a2245f576deb91049354635887c62eeb22969ef63a7b5fc2c53701b067dcc9425e11dac183f3328c4b64dd6493b454b09b9d24e228acd8f8795ce673b4804549a4c9de6dca9511252bb5e975302030100010281800b95c2658b4823c863d2ec9a8a8320c153fe737734ab60b6bdae4817aa79011106f63dd6fbd4df300c69dfe1927e02a41a4127ec8bdad377aa8179edd0bc683b7c491d7f26016600750725bcc2b3138ac3c84c8eb47fa59bc30c517ca212d6ba0d841ceb7baed795a9a007767a8d59faeb68c28367f82925593a2b6f04c23561024100cdd1a3829426ab3c8d765c996d44cc90140150cf9972f408025f70b3707d1e625c9e25fde646641752633f55d25379574f10cc3bf73ebb42b4d9c95b62867d39024100fd2dedb0a58f4f8e416574c0da602318fb5c0e02569ac9f2d157bb4bea4ba73b45740d53b6496409c3c2c658558ad0c58a9ca624c940e537c8d93f46ac5ac4eb024007d6b4238500f4049a5ea7a830412e894e39be9a297df74d56c9cbc109c7ba2084e6810bea7943d69f8ca81cdca5d1394209a1bda6ecfcb4cdae7dbcbd43e20102400ecdb8b0337e05b0d3b212f993cb3b4222b067414bbf113fd96dbfcdd88d43e1fb55a5d1d73ec352aed79cb15d8f1855f49ce43a126a70fcaa09c9e160028eb10240686c70c1cad0a791c41dfbc226c19436f9ccc18bab480bfbbc0322782dff73a2248acfedddaba4f1cf22fa8fa34815803e80b2e9b2f94f63695b0d8217d983e8")
    