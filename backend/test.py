from lib.blockchain import Blockchain
from lib.taskThread import TaskThread
from lib.mining_thread import MiningThread

blockchain = Blockchain()
miningThread = MiningThread(blockchain, "", "")
taskThread = TaskThread(blockchain, "", "", 5000)

print(blockchain.forks)
print(miningThread.blockchain.forks)
print(taskThread.blockchain.forks)

blockchain.forks = ["test"]

print(blockchain.forks)
print(miningThread.blockchain.forks)
print(taskThread.blockchain.forks)