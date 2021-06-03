from __future__ import annotations

from hashlib import sha256
from typing import Dict, OrderedDict
import json

class Task:
    def __init__(self, resourceURL: str, threshold: float, maxEpochs: int, publicKey: str, signature:str):
        self.type = "task"
        self.resourceURL = resourceURL
        self.threshold = round(threshold,2)
        self.maxEpochs = maxEpochs
        self.publicKey = publicKey
        self.signature = signature
        assert threshold >50 and threshold <80

    def toDict(self) -> OrderedDict:
        return OrderedDict({
            "type": self.type,
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
            if(self.resourceURL == o.resourceURL and self.threshold == o.threshold and self.maxEpochs == o.maxEpochs and self.publicKey == o.publicKey and self.signature == o.signature):
                return True
        return False

    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())
        
    def getUnsignedStr(self) -> str:
        dict = json.loads(str(self))
        dict["signature"] = ""
        return json.dumps(dict, default=lambda o: o.toDict())

    @classmethod
    def fromDict(cls, dict: Dict) -> Task:
        return cls(dict["resourceURL"], dict["threshold"], dict["maxEpochs"], dict["publicKey"], dict["signature"])

class TaskSolution:
    def __init__(self, taskId: str, modelURL: str, accuracy: float, wst: int, publicKey: str, signature:str):
        self.type = "taskSolution"
        self.taskId = taskId
        self.modelURL = modelURL
        self.accuracy = round(accuracy,2)
        self.wst = wst
        self.publicKey = publicKey
        self.signature = signature

    def toDict(self) -> OrderedDict:
        return OrderedDict({
            "type": self.type,
            "taskId": self.taskId,
            "modelURL": self.modelURL,
            "accuracy": self.accuracy,
            "wst": self.wst,
            "publicKey": self.publicKey,
            "signature": self.signature
        })

    def getHash(self) -> str:
        return sha256(bytes(str(self),encoding='utf-8')).hexdigest()

    def __eq__(self, o: object) -> bool:
        if (isinstance(o, TaskSolution)):
            if(self.taskId == o.taskId and self.modelURL == o.modelURL and self.accuracy == o.accuracy and self.wst == o.wst and self.publicKey == o.publicKey and self.signature == o.signature):
                return True
        return False

    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())
    
    def getUnsignedStr(self) -> str:
        dict = json.loads(str(self))
        dict["signature"] = ""
        return json.dumps(dict, default=lambda o: o.toDict())

    @classmethod
    def fromDict(cls, dict: Dict) -> TaskSolution:
        return cls(dict["taskId"], dict["modelURL"], dict["accuracy"], dict["wst"], dict["publicKey"], dict["signature"])
        