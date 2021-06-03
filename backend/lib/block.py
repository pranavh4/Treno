from __future__ import annotations
from .task import TaskSolution, Task

from .transaction import Transaction
from hashlib import sha256
from typing import Dict, List, OrderedDict
from .utils import generateSignature
import time
import json

class Block:
    def __init__(self, transactions: list, prevBlockHash: str, generatorPubKey: str, generationSignature: str, baseTarget: int, cumulativeDifficulty: int, timestamp: int = int(time.time()), signature: str = ''):
        self.transactions = transactions
        self.prevBlockHash = prevBlockHash
        self.timestamp = timestamp
        self.baseTarget = baseTarget
        self.generationSignature = generationSignature
        self.cumulativeDifficulty = cumulativeDifficulty
        self.generatorPubKey = generatorPubKey
        self.signature = signature

    def getHash(self) -> str:
        return sha256(bytes(str(self),encoding='utf-8')).hexdigest()
        
    def signBlock(self, privateKey):
        self.signature = generateSignature(self.getUnsignedStr(), privateKey)
    
    def toDict(self) -> OrderedDict:
        return OrderedDict({
                "prevBlockHash":self.prevBlockHash,
                "timestamp":self.timestamp,
                "baseTarget": self.baseTarget,
                "generationSignature": self.generationSignature,
                "cumulativeDifficulty": self.cumulativeDifficulty,
                "generatorPubKey": self.generatorPubKey,
                "signature": self.signature,
                "transactions":[t.toDict() for t in self.transactions]
        })

    def getUnsignedStr(self):
        dict = self.toDict()
        del dict["signature"]
        return json.dumps(dict, default=lambda o: o.toDict())
    
    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())

    @classmethod
    def fromDict(cls, Dict: dict) -> Block:
        if Dict==None:
            return None
        transactions=[]
        for transaction in Dict["transactions"]:
            if transaction["type"]=="currency":
                transactions.append(Transaction.fromDict(transaction))
            elif transaction["type"]=="taskSolution":
                transactions.append(TaskSolution.fromDict(transaction))
            elif transaction["type"]=="task":
                transactions.append(Task.fromDict(transaction))
        # transactions = [Transaction.fromDict(t) for t in Dict["transactions"]]
        if "timestamp" in Dict:
            return cls(            
                transactions,
                Dict["prevBlockHash"],
                Dict["generatorPubKey"],
                Dict["generationSignature"],
                Dict["baseTarget"],
                Dict["cumulativeDifficulty"],
                Dict["timestamp"],
                Dict["signature"]
            )
        return cls(
            transactions,
            Dict["prevBlockHash"],
            Dict["generatorPubKey"],
            Dict["generationSignature"],
            Dict["baseTarget"],
            Dict["cumulativeDifficulty"]
        )
