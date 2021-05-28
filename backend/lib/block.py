from __future__ import annotations

from .transaction import Transaction
from hashlib import sha256
from typing import Dict, List, OrderedDict
from .utils import generateSignature
import time
import json

class Block:
    def __init__(self, transactions: list, prevBlockHash: str, generatorPubKey: str, generationSignature: str, baseTarget: int, cumulativeDifficulty: int):
        self.transactions = transactions
        self.prevBlockHash = prevBlockHash
        self.timestamp = str(int(time.time()))
        self.baseTarget = baseTarget
        self.generationSignature = generationSignature
        self.cumulativeDifficulty = cumulativeDifficulty
        self.generatorPubKey = generatorPubKey
        self.signature = ''

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
                "transactions":self.transactions
        })

    def getUnsignedStr(self):
        dict = self.toDict()
        del dict["signature"]
        return json.dumps(dict, default=lambda o: o.toDict())
    
    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())

    @classmethod
    def fromDict(cls, dict: Dict) -> Block:
        transactions = [Transaction.fromDict(t) for t in dict["transactions"]]
        return cls(
            transactions,
            dict["prevBlockHash"],
            dict["baseTarget"],
            dict["generationSignature"],
            dict["cumulativeDifficulty"],
            dict["generatorPubKey"]
        )
