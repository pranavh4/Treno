import tensorflow as tf
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.optimizers import SGD, Adam
from task import Task, TaskSolution
import pandas as pd
import numpy as np
from pyunpack import Archive
from pathlib import Path
import wget

# Task:
#     |
#     |---data
#     |   |---train.csv
#     |   |---test.csv
#     |
#     |---model
#     |
#     |---config.json


class TaskService:
    
    downloadFolder = "../../downloads"
    solutionFolder = "../../solutions"
    taskFolder = "../../currentTask"
    uploadCmd = "curl  --upload-file {fileLoc} https://transfer.sh/task" 

    @staticmethod
    def createTask(task: Task):
        return ""
    
    @staticmethod
    def downloadTask(taskURL: str) -> str:
        Path(TaskService.downloadFolder).mkdir(parents=True, exist_ok=True)
        Path(TaskService.taskFolder).mkdir(parents=True, exist_ok=True)
        file = wget.download(taskURL,out=TaskService.downloadFolder +"/" + taskURL.split('/')[-1] )       
        #unzip to taskFolder
        Archive(file).extractall(TaskService.taskFolder)
        return file

    @staticmethod
    def mine():
        try:
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

            #callback to save best acc mdodel
            checkpointer = ModelCheckpoint(
                filepath= TaskService.solutionFolder + '/solution.hdf5', 
                verbose=1, 
                save_best_only=True,
                save_weights_only=True, 
                monitor='val_accuracy'
            )

            mlModel.compile(
                loss='categorical_crossentropy',
                optimizer=Adam(learning_rate=0.001),
                metrics=['accuracy']
            )

            print("Starting to Mine...")
            history = mlModel.fit(
                xTrain,
                yTrainCat,
                batch_size=32,
                epochs=1,
                validation_data=(xTest,yTestCat),
                verbose=1,
                callbacks=[checkpointer]
            )
            print("Completed Mining..", history.history)

        except Exception as e:
            print("Error occured while mining..\n", e)
  
    @staticmethod
    def verifyFiles() -> bool:
        try:
            mlModel = tf.keras.models.load_model(TaskService.taskFolder+'/model')
            train = pd.read_csv('../../currentTask/data/train.csv',  header=None)   
            test = pd.read_csv('../../currentTask/data/test.csv',  header=None)   
            return True
        except:
            print("File verification unsuccessful")
            return False

if __name__ == "__main__":
    TaskService.downloadTask("https://transfer.sh/jX/poker.zip")
    TaskService.mine()
