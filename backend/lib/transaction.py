import binascii
from typing import OrderedDict
import time
import json
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA

class Transaction:
    def __init__(self,sender,receiver,amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = str(int(time.time()))
        self.signature = ""

    def signTransaction(self, private_key):
        private_key = RSA.importKey(binascii.unhexlify(private_key))
        signer = PKCS1_v1_5.new(private_key)
        h = SHA.new(str(self.toUnsignedStr()).encode('utf8'))
        self.signature = binascii.hexlify(signer.sign(h)).decode('ascii')

    def validateSignature(self) -> bool:
        public_key = RSA.importKey(binascii.unhexlify(self.sender))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA.new(str(self.toUnsignedStr()).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(self.signature))

    def toUnsignedStr(self) -> str:
        dict = self.toDict()
        del dict['signature']
        return json.dumps(dict)

    def toDict(self) -> OrderedDict:
        return OrderedDict({
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "signature": self.signature
        })

    def __str__(self) -> str:
        return json.dumps(self, default=lambda o: o.toDict())
