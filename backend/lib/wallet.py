from os import stat
from typing import Dict
import binascii
import Crypto
from Crypto.PublicKey import RSA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
import binascii

from flask import json
from .transaction import Transaction, TransactionInput, TransactionOutput

class Wallet:
    @staticmethod
    def generateKey() -> Dict:
        random_gen = Crypto.Random.new().read
        private_key = RSA.generate(1024, random_gen)
        public_key = private_key.publickey()
        keys = {
            'privateKey': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
            'publicKey': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
        }
        return keys

    @staticmethod
    def createTransaction(utxos, sender, receiver, amount, transactionFee, privateKey) -> Dict:
        #find utxo from pool that satisfies required itxo
        #create utxo for receiver and for change
        #verify transaction and add to pool
        #remove old utxo and add new utxo
        utxoAmt = 0
        txIn = []
        for utxo in utxos:
            signature = Wallet.signTransaction(utxo["txId"], privateKey)
            txIn.append(TransactionInput(
                utxo["txId"],
                utxo["outputIndex"],
                signature
            ))
            pitx = TransactionInput(
                utxo["txId"],
                utxo["outputIndex"],
                signature
            )
            print(pitx)
            utxoAmt += utxo["amount"]
            if utxoAmt >= amount + transactionFee:
                break
        else:
            return None

        change = utxoAmt - (amount + transactionFee)
        txOut = [
            TransactionOutput(amount, receiver),
            TransactionOutput(change, sender)
        ]

        transaction = Transaction(txIn, txOut)
        return json.loads(str(transaction)) 
    
    @staticmethod
    def signTransaction(txId, privateKey):
        privateKey = RSA.importKey(binascii.unhexlify(privateKey))
        signer = PKCS1_v1_5.new(privateKey)
        h = SHA.new(txId.encode('utf8'))
        return binascii.hexlify(signer.sign(h)).decode('ascii')