import time
from .blockchain import Blockchain
from .taskService import TaskService
from threading import Thread
import random
class TaskThread(Thread):
    def __init__(self, blockchain: Blockchain, publicKey: str, privateKey: str):
        self.blockchain = blockchain
        self.publicKey = publicKey
        self.privateKey = privateKey

    def run(self):
        while True:
            random.seed(self.publicKey + str(int(time.time())), version=2)
            tasks = [self.blockchain.untrainedTasks[tId] for tId in self.blockchain.untrainedTasks.keys()]
            index = random.randrange(0, len(tasks))
            task = tasks[index]
            TaskService.downloadTask(task)
            taskSol = TaskService.runTask(task)
            self.blockchain.addTaskSolution(taskSol)