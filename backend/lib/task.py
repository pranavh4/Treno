from __future__ import annotations

from hashlib import sha256
from typing import Dict, OrderedDict
import json
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
import time

class Task:
    def __init__(self, resourceURL: str, threshold: float, maxEpochs: int, publicKey: str, signature:str):
        self.timestamp = int(time.time())
        self.resourceURL = resourceURL
        self.threshold = round(threshold,2)
        self.maxEpochs = maxEpochs
        self.publicKey = publicKey
        self.signature = signature
        assert threshold >50 and threshold <80

    def toDict(self) -> OrderedDict:
        return OrderedDict({
            "timestamp": self.timestamp,
            "resourceURL": self.resourceURL,
            "threshold": self.threshold,
            "maxEpochs": self.maxEpochs,
            "publicKey": self.publicKey,
            "signature": self.signature
        })

    def getHash(self) -> str:
        return sha256(bytes(str(self),encoding='utf-8')).hexdigest()

    def __eq__(self, o: object) -> bool:
        if (isinstance(o, Task)):
            if(self.timestamp == o.timestamp and self.resourceURL == o.resourceURL and self.threshold == o.threshold and self.maxEpochs == o.maxEpochs and self.publicKey == o.publicKey and self.signature == o.signature):
                return True
        return False

    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())
    
    @classmethod
    def fromDict(cls, dict: Dict) -> Task:
        return cls(dict["timestamp"], dict["resourceURL"], dict["threshold"], dict["maxEpochs"], dict["publicKey"], dict["signature"])

class TaskSolution:
    def __init__(self, task: Task, modelURL: str, accuracy: float, publicKey: str, signature:str):
        self.timestamp = int(time.time())
        self.taskId = task.getHash()
        self.modelURL = modelURL
        self.accuracy = round(accuracy,2)
        self.wst = 0
        self.publicKey = publicKey
        self.signature = signature

    def toDict(self) -> OrderedDict:
        return OrderedDict({
            "timestamp": self.timestamp,
            "taskId": self.taskId,
            "modelURL": self.modelURL,
            "accuracy": self.accuracy,
            "wst": self.wst,
            "publicKey": self.publicKey,
            "signature": self.signature
        })

    def __eq__(self, o: object) -> bool:
        if (isinstance(o, TaskSolution)):
            if(self.timestamp == o.timestamp and self.taskId == o.taskId and self.modelURL == o.modelURL and self.accuracy == o.accuracy and self.wst == o.wst and self.publicKey == o.publicKey and self.signature == o.signature):
                return True
        return False

    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())
    
    def getUnsignedStr(self) -> str:
        dict = json.loads(str(self))
        print(dict)
        return json.dumps(dict, default=lambda o: o.toDict())

    @classmethod
    def fromDict(cls, dict: Dict) -> TaskSolution:
        return cls(dict["timestamp"], dict["taskId"], dict["modelURL"], dict["accuracy"], dict["wst"], dict["publicKey"], dict["signature"])
        