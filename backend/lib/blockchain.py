from .task import Task, TaskSolution
from .taskService import TaskService
from typing import Dict
from .block import Block
from pathlib import Path
from .transaction import Transaction, TransactionInput, TransactionOutput
from .utils import validateSignature
from .block_verification_utils import *
import json


class Blockchain:
    MAX_COINS = 5000000
    MIN_TRANSACTION_FEE = 1
    MAX_CURRENCY_TRANSACTION_IN_BLOCK = 49
    MAX_WST_IN_BLOCK = 50
    MAX_TASK_REQUESTS_IN_BLOCK = 50
    WST_AGE_LIMIT = 10000

    def __init__(self):
        self.mainChain = []
        self.forks = []
        self.blocks = {}
        self.transactionPool = {}
        self.utxoPool = {}
        self.taskPool = {}
        self.wstPool = {}
        self.untrainedTasks = {}

    def createGenesisBlock(self):
        genesisKeyPath = Path(__file__).parent / "resources/genesisKey.json"
        with genesisKeyPath.open() as f:
            genesisKey = json.load(f)
        
        transaction = Transaction(
            [TransactionInput("0",-1, "0")],
            [TransactionOutput(self.MAX_COINS, genesisKey["publicKey"])]
        )

        wst = TaskSolution("0","0",0.0,1,genesisKey["publicKey"],"0")
        # print(transaction)
        block = Block(
            [transaction, wst] ,
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
           
    def addBlock(self, block: Block) -> bool:
        valid = self.verifyBlock(block)
        if not valid:
            return False
        blockHash = block.getHash()
        self.mainChain.append(blockHash)
        self.blocks[blockHash] = block

        if len(block.transactions):
            if self.hasCurrencyTransactions(block):
                coinbaseTx = block.transactions[0]
                self.addUTXO(
                    coinbaseTx.getHash(),
                    0,
                    coinbaseTx.txOut[0].amount,
                    coinbaseTx.txOut[0].receiver
                )

            for tx in block.transactions[1:]:
                if tx.type == "currency":
                    del self.transactionPool[tx.getHash()]
                elif tx.type == "task":
                    del self.taskPool[tx.getHash()]
                else:
                    del self.wstPool[tx.getHash()]
        return True

    def verifyBlock(self, block: Block) -> bool:
        minerKey = block.generatorPubKey
        effectiveBalance = self.getWSTBalance(self.mainChain.index(block.prevBlockHash), minerKey)
        prevBlock = self.blocks[block.prevBlockHash]
        hitTime = block.timestamp - prevBlock.timestamp
        blocks = [self.blocks[block.prevBlockHash]]
        while len(blocks)!=4:
            if blocks[0].prevBlockHash == "0":
                break
            b = self.blocks[blocks[0].prevBlockHash]
            blocks = [b] + blocks
        if not verifyHit(hitTime, effectiveBalance, prevBlock, block.timestamp):
            print("Hit time Invalid")
            return False
        if not validateSignature(block.getUnsignedStr(), block.generatorPubKey, block.signature):
            print("signature invalid")
            return False
        if not verifyBaseTarget(blocks, block):
            print("base target invalid")
            return False
        if not verifyCumulativeDifficulty(block, prevBlock):
            print("cumulative difficulty invalid")
            return False
        if not verifyGenerationSignature(block, prevBlock):
            print("generation signature invalid")
            return False
        if len(block.transactions)==0:
            return True
        if self.hasCurrencyTransactions(block) and not self.verifyCoinbase(block):
            print("Coinbase invalid")
            return False

        for tx in block.transactions[1:]:
            if tx.type == "currency":
                if tx.getHash() not in self.transactionPool.keys():
                    sender = self.findByTxid(tx.txIn[0].txId).txOut[tx.txIn[0].outputIndex].receiver
                    self.addTransaction(tx, sender)
                if not self.verifyTransaction(tx, True):
                    print("transaction invalid")
                    return False
            elif tx.type == "task":
                if tx.getHash() not in self.taskPool.keys():
                    if not self.addTask(tx):
                        print("task invalid")
                        return False
            else:
                if tx.getHash() not in self.wstPool.keys():
                    if not self.addTaskSolution(tx):
                        print("task solution invalid")
                        return False
        return True

    def popLastBlock(self):
        block = self.blocks[self.mainChain[-1]]
        for tx in block.transactions:
            if tx.type == "currency":
                self.transactionPool[tx.getHash()] = tx
            elif tx.type == "task":
                self.taskPool[tx.getHash()] = tx
            else:
                self.wstPool[tx.getHash()] = tx
        self.mainChain.pop() 

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

    def addTask(self, task: Task) -> bool:
        valid = TaskService.validateTask(task)
        if not valid:
            return False
        self.taskPool[task.getHash()] = task
        return True

    def addTaskSolution(self, taskSolution: TaskSolution) -> bool:
        task = self.findByTxid(taskSolution.taskId)
        if task == None or task.type != "task":
            return False
        valid = TaskService.validateTaskSolution(task, taskSolution)
        if not valid:
            return False
        self.wstPool[taskSolution.getHash()] = taskSolution
        del self.untrainedTasks[taskSolution.taskId]
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
            if not validateSignature(transaction.getUnsignedStr() + input.txId + str(input.outputIndex), signer, input.signature):
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
        txIds = [t.getHash() for t in block.transactions[1:] if t.type == "currency"]
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

    def findByTxid(self, txId: str):
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

    def getWSTBalance(self, height: int, pubKey: str) -> int:
        startIndex = height - self.WST_AGE_LIMIT
        startIndex = startIndex if startIndex > 0 else 0
        blockIds = self.mainChain[startIndex : height + 1]
        wstBalance = 0
        for bId in blockIds:
            block = self.blocks[bId]
            for tx in block.transactions:
                if tx.type == 'taskSolution':
                    if tx.publicKey == pubKey:
                        wstBalance += tx.wst
        print("wst balance: " + str(wstBalance))
        return wstBalance

    @staticmethod
    def hasCurrencyTransactions(block: Block) -> bool:
        return len([t for t in block.transactions if t.type=="currency"]) > 0