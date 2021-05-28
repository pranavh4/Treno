import threading
from typing import List
from .blockchain import Blockchain

class MiningThread(threading.Thread):
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain

    def run():
        return 
