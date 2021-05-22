from hashlib import sha256
from typing import OrderedDict
import time
import json

class Block:
    def __init__(self, transactions, prevBlockHash):
        self.transactions = transactions
        self.prevBlockHash = prevBlockHash
        self.timestamp = str(int(time.time()))

    def getHash(self) -> str:
        return sha256(bytes(str(self),encoding='utf-8')).hexdigest()
    
    def toDict(self) -> OrderedDict:
        return OrderedDict({
                "prevBlockHash":self.prevBlockHash,
                "timestamp":self.timestamp,
                "transactions":self.transactions
        })
    
    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())