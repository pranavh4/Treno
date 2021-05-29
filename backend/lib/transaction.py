from __future__ import annotations

import binascii
from hashlib import sha256
from typing import Dict, OrderedDict
import json
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA

class TransactionInput:
    def __init__(self, txId: str, outputIndex: int, signature: str):
        self.txId = txId
        self.outputIndex = outputIndex
        self.signature = signature

    def toDict(self) -> OrderedDict:
        return OrderedDict({
            "txId": self.txId,
            "outputIndex": self.outputIndex,
            "signature": self.signature
        })

    def __eq__(self, o: object) -> bool:
        if (isinstance(o, TransactionInput)):
            if(self.txId == o.txId and self.outputIndex == o.outputIndex and self.signature == o.signature):
                return True
        return False

    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())
    
    @classmethod
    def fromDict(cls, dict: Dict) -> TransactionInput:
        return cls(dict["txId"], dict["outputIndex"], dict["signature"])

class TransactionOutput:
    def __init__(self, amount: int, receiver: str):
        self.amount = amount
        self.receiver = receiver
    
    def toDict(self) -> OrderedDict:
        return OrderedDict({
            "amount":self.amount,
            "receiver":self.receiver
        })

    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())

    @classmethod
    def fromDict(cls, dict: Dict) -> TransactionOutput:
        return cls(dict["amount"], dict["receiver"])

class Transaction:
    def __init__(self, txIn, txOut):
        self.txIn = txIn
        self.txOut = txOut
        self.type = "currency"

    def getHash(self) -> str:
        return sha256(bytes(str(self),encoding='utf-8')).hexdigest()

    def toDict(self) -> OrderedDict:
        return OrderedDict({
            "type": self.type,
            "txIn": self.txIn,
            "txOut": self.txOut
        })
    
    @classmethod
    def fromDict(cls, dict: Dict) -> Transaction:
        txIn = [TransactionInput.fromDict(t) for t in dict["txIn"]]
        txOut = [TransactionOutput.fromDict(t) for t in dict["txOut"]]
        return cls(txIn, txOut)

    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())
