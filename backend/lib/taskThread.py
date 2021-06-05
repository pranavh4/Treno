import time
from .blockchain import Blockchain
from .taskService import TaskService
from threading import Thread
import random
from .p2p import P2P
class TaskThread(Thread):
    def __init__(self, blockchain: Blockchain, publicKey: str, privateKey: str):
        super().__init__()
        self.blockchain = blockchain
        self.publicKey = publicKey
        self.privateKey = privateKey

    def run(self):
        while True:
            random.seed(self.publicKey + str(int(time.time())), version=2)
            tasks = [self.blockchain.untrainedTasks[tId] for tId in self.blockchain.untrainedTasks.keys()]
            if tasks:
                index = random.randrange(0, len(tasks))
                task = tasks[index]
                TaskService.downloadTask(task)
                taskSol = TaskService.runTask(task, self.publicKey, self.privateKey)
                self.blockchain.addTaskSolution(taskSol)
                P2P.broadcastTaskSolution(taskSol)
            else:
                time.sleep(1)