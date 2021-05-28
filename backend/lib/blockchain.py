from time import time
from typing import Dict
from .block import Block
from hashlib import sha256
from pathlib import Path
from .transaction import Transaction, TransactionInput, TransactionOutput
from .utils import validateSignature
import json


class Blockchain:
    MAX_COINS = 5000000
    MIN_TRANSACTION_FEE = 1
    MAX_TRANSACTION_IN_BLOCK = 49

    def __init__(self):
        self.mainChain = []
        self.secondaryChain = []
        self.blocks = {}
        self.transactionPool = {}
        self.utxoPool = {}

    def createGenesisBlock(self):
        genesisKeyPath = Path(__file__).parent / "resources/genesisKey.json"
        with genesisKeyPath.open() as f:
            genesisKey = json.load(f)
        
        transaction = Transaction(
            [TransactionInput("0",-1, "0")],
            [TransactionOutput(self.MAX_COINS, genesisKey["publicKey"])]
        )
        # print(transaction)
        block = Block(
            [transaction],
            "0",
            genesisKey["publicKey"],
            "0000000000000000000000000000000000000000000000000000000000000000",
            153722867,
            0
            )
        block.signBlock(genesisKey["privateKey"])
        blockHash = block.getHash()

        self.blocks = {blockHash: block}
        self.mainChain = [blockHash]
        self.utxoPool[genesisKey["publicKey"]] = [{
            "txId": transaction.getHash(),
            "outputIndex": 0,
            "amount": self.MAX_COINS
        }]
    
    def createBlock(self, miner):
        txIds = self.transactionPool.keys()
        prevBlockHash = self.blocks[self.mainChain[-1]].getHash()
        if len(txIds) == 0:
            return Block([],prevBlockHash)

        sortedTransactions = sorted(
            [self.transactionPool[txId] for txId in txIds],
            key = lambda t:t["transactionFee"], 
            reverse=True
        )
        blockTransactions = [t["transaction"] for t in sortedTransactions[:self.MAX_TRANSACTION_IN_BLOCK]]

        minerReward = sum([t["transactionFee"] for t in sortedTransactions[:self.MAX_TRANSACTION_IN_BLOCK]])
        coinbaseTransaction = Transaction(
            [TransactionInput("0",-1,"Coinbase Transaction")],
            [TransactionOutput(minerReward, miner)]
        )
        blockTransactions = [coinbaseTransaction] + blockTransactions
        block = Block(blockTransactions,prevBlockHash)
        return block        

    def addBlock(self, block: Block) -> bool:
        valid = self.verifyBlock(block)
        if not valid:
            return False
        blockHash = block.getHash()
        self.mainChain.append(blockHash)
        self.blocks[blockHash] = block

        if len(block.transactions):
            coinbaseTx = block.transactions[0]
            self.addUTXO(
                coinbaseTx.getHash(),
                0,
                coinbaseTx.txOut[0].amount,
                coinbaseTx.txOut[0].receiver
            )

            for tx in block.transactions[1:]:
                del self.transactionPool[tx.getHash()]
        return True

    def verifyBlock(self, block: Block) -> bool:
        if len(block.transactions)==0:
            return True
        if not self.verifyCoinbase(block):
            print("Coinbase invalid")
            return False

        for tx in block.transactions[1:]:
            independentlyVerified = tx.getHash() in self.transactionPool.keys()
            if not self.verifyTransaction(tx, independentlyVerified):
                print("transaction invalid")
                return False
        return True

    def addTransaction(self, transaction: Transaction, sender: str) -> bool:
        valid = self.verifyTransaction(transaction)
        if not valid["valid"]:
            return False
        utxos = self.utxoPool[sender]
        for txIn in transaction.txIn:
            inputTx = self.findByTxid(txIn.txId)
            utxo = {
                "txId": txIn.txId,
                "outputIndex": txIn.outputIndex,
                "amount": inputTx.txOut[txIn.outputIndex].amount
            }
            if utxo in utxos:
                utxos.remove(utxo)

        for index, txOut in enumerate(transaction.txOut):
            # utxo = {
            #     "txId": transaction.getHash(),
            #     "outputIndex": index,
            #     "amount": txOut.amount
            # }
            # if txOut.receiver not in self.utxoPool.keys():
            #     self.utxoPool[txOut.receiver] = [utxo]
            # else:
            #     self.utxoPool[txOut.receiver].append(utxo)
            self.addUTXO(
                transaction.getHash(),
                index,
                txOut.amount,
                txOut.receiver
            )
        
        self.transactionPool[transaction.getHash()] = {"transaction":transaction,"transactionFee": valid["transactionFee"]}

        return True

    def verifyTransaction(self, transaction: Transaction, txIndependentlyVerified=False) -> Dict:
        inputAmt = 0
        for input in transaction.txIn:
            if input.txId == "0":
                print("txId = 0 can only exist for coinbase transaction")
                return {"valid":False}
            inputTx = self.findByTxid(input.txId)
            if inputTx == None:
                print("no input tx")
                return {"valid":False}
            outputTx = inputTx.txOut[input.outputIndex]
            signer = outputTx.receiver
            if not validateSignature(inputTx.getHash(), signer, input.signature):
                print("signature not valid")
                return {"valid":False}
            if self.utxoSpent(signer, input.txId, input.outputIndex, outputTx.amount) and not txIndependentlyVerified:
                print("utxo already spent")
                return {"valid":False}
            inputAmt += outputTx.amount
        
        if inputAmt > self.MAX_COINS:
            print("Input greater than max coins")
            return {"valid":False}
        
        outputAmt = 0
        for outputTx in transaction.txOut:
            outputAmt += outputTx.amount
        
        if inputAmt < outputAmt:
            print("Insufficient Funds")
            return {"valid":False}
        
        if (inputAmt - outputAmt) < self.MIN_TRANSACTION_FEE:
            print("No transaction fees")
            return {"valid":False}
        
        return {"transactionFee": inputAmt - outputAmt, "valid":True}

    def verifyCoinbase(self, block: Block) -> bool:
        coinbaseTx = block.transactions[0]
        if len(coinbaseTx.txIn) != 1 or len(coinbaseTx.txOut) != 1:
            return False
        if coinbaseTx.txIn[0].txId!="0":
            return False
        coinbaseAmt = coinbaseTx.txOut[0].amount
        txIds = [t.getHash() for t in block.transactions[1:]]
        try:
            minerReward = sum([self.transactionPool[txId]["transactionFee"] for txId in txIds])
        except:
            return False
        if minerReward!=coinbaseAmt:
            return False
        return True

    def utxoSpent(self, sender, txId, outputIndex, amount) -> bool:
        # for blockHash in self.mainChain:
        #     block = self.blocks[blockHash]
        #     for transaction in block.transactions:
        #         for iTx in transaction.txIn:
        #             if inputTx == iTx:
        #                 return True

        # for key in self.transactionPool.keys():
        #     transaction = self.transactionPool[key]
        #     for iTx in transaction.txIn:
        #         if inputTx == iTx:
        #             return True
        utxo = {
            "txId": txId, 
            "outputIndex": outputIndex,
            "amount":amount
        }
        if utxo not in self.utxoPool[sender]:
            return True
        return False

    def findByTxid(self, txId: str) -> Transaction:
        print(self.mainChain)
        for blockHash in self.mainChain:
            block = self.blocks[blockHash]
            print(block)
            for transaction in block.transactions:
                txHash = transaction.getHash()
                print(txHash,txId)
                if txHash == txId:
                    return transaction
        
        try:
            transaction = self.transactionPool[txId]["transaction"]
            return transaction
        except:
            pass

            return None        

    def addUTXO(self, txId, outputIndex, amount, receiver):
        utxo = {
            "txId": txId,
            "outputIndex": outputIndex,
            "amount": amount
        }
        if receiver not in self.utxoPool.keys():
            self.utxoPool[receiver] = [utxo]
        else:
            self.utxoPool[receiver].append(utxo)