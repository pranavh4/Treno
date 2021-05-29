from __future__ import annotations

from hashlib import sha256
from typing import Dict, OrderedDict
import json
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
import time

class Task:
    def __init__(self, resourceURL: str, threshold: float, signature:str):
        self.date = int(time.time())
        self.resourceURL = resourceURL
        self.threshold = round(threshold,2)
        self.signature = signature
        assert threshold >50 and threshold <100

    def toDict(self) -> OrderedDict:
        return OrderedDict({
            "date": self.date,
            "resourceURL": self.resourceURL,
            "threshold": self.threshold,
            "signature": self.signature
        })

    def getHash(self) -> str:
        return sha256(bytes(str(self),encoding='utf-8')).hexdigest()

    def __eq__(self, o: object) -> bool:
        if (isinstance(o, Task)):
            if(self.date == o.date and self.resourceURL == o.resourceURL and self.threshold == o.threshold and self.signature == o.signature):
                return True
        return False

    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())
    
    @classmethod
    def fromDict(cls, dict: Dict) -> Task:
        return cls(dict["date"], dict["resourceURL"], dict["threshold"], dict["signature"])

class TaskSolution:
    def __init__(self, task: Task, modelURL: str, accuracy: float, signature:str):
        self.date = int(time.time())
        self.taskHash = task.getHash()
        self.modelURL = modelURL
        self.accuracy = round(accuracy,2)
        self.signature = signature

    def toDict(self) -> OrderedDict:
        return OrderedDict({
            "date": self.date,
            "taskHash": self.taskHash,
            "modelURL": self.modelURL,
            "accuracy": self.accuracy,
            "signature": self.signature
        })

    def __eq__(self, o: object) -> bool:
        if (isinstance(o, TaskSolution)):
            if(self.date == o.date and self.taskHash == o.taskHash and self.modelURL == o.modelURL and self.accuracy == o.accuracy and self.signature == o.signature):
                return True
        return False

    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())
    
    @classmethod
    def fromDict(cls, dict: Dict) -> TaskSolution:
        return cls(dict["date"], dict["taskHash"], dict["modelURL"], dict["accuracy"], dict["signature"])
