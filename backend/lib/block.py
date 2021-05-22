from hashlib import sha256
from typing import OrderedDict
import time
import json

class Block:
    def __init__(self, transactions, prevBlock):
        self.transactions = transactions
        prevBlockStr = str(prevBlock)
        self.prevBlockHash = sha256(bytes(prevBlockStr,encoding='utf-8')).hexdigest()
        self.timestamp = str(int(time.time()))
    
    def toDict(self) -> OrderedDict:
        return OrderedDict({
                "prevBlockHash":self.prevBlockHash,
                "timestamp":self.timestamp,
                "transactions":self.transactions
        })
    
    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())