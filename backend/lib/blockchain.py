from threading import get_ident
from .task import Task, TaskSolution
from .taskService import TaskService
from typing import Dict
from .block import Block
from pathlib import Path
from .transaction import Transaction, TransactionInput, TransactionOutput
from .utils import validateSignature, bcolors
from .block_verification_utils import *
import json


class Blockchain:
    MAX_COINS = 5000000
    MIN_TRANSACTION_FEE = 1
    MAX_CURRENCY_TRANSACTION_IN_BLOCK = 49
    MAX_WST_IN_BLOCK = 50
    MAX_TASK_REQUESTS_IN_BLOCK = 50
    WST_AGE_LIMIT = 10000
    GENESIS_NODE_TIMESTAMP = None

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
        MinerPath = Path(__file__).parent / "resources/miner5001.json"
        with genesisKeyPath.open() as f:
            genesisKey = json.load(f)
        with MinerPath.open() as f:
            MinerKey = json.load(f)
        transaction = Transaction(
            [TransactionInput("0",-1, "0")],
            [TransactionOutput(self.MAX_COINS, genesisKey["publicKey"])]
        )

        wst = TaskSolution("0","0",0.0,1,genesisKey["publicKey"],"0")
        wstMiner = TaskSolution("0","0",0.0,1,MinerKey["publicKey"],"0")
        # print(transaction)
        block = Block(
            [transaction, wst, wstMiner] ,
            "0",
            genesisKey["publicKey"],
            "0000000000000000000000000000000000000000000000000000000000000000",
            153722867,
            0,
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
        lastBlockPopped = False
        lastBlock = self.blocks[self.mainChain[-1]]
        if block.prevBlockHash != self.mainChain[-1]:
            if block.prevBlockHash != self.mainChain[-2]:
                return False
            if block.timestamp > lastBlock.timestamp:
                return False
            elif block.timestamp == lastBlock.timestamp and block.cumulativeDifficulty < lastBlock.cumulativeDifficulty:
                return False
            self.popLastBlock()
            lastBlockPopped = True
        valid = self.verifyBlock(block)
        if not valid:
            if lastBlockPopped:
                self.addBlock(lastBlock)
            return False
        if lastBlockPopped:
            print(f"{bcolors.WARNING}Popped last block and adding received block{bcolors.ENDC}")
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

            for tx in block.transactions:
                if tx.type == "currency" and tx.txIn[0].outputIndex!= -1:
                    del self.transactionPool[tx.getHash()]
                elif tx.type == "task":
                    del self.taskPool[tx.getHash()]
                elif tx.type == "taskSolution":
                    del self.wstPool[tx.getHash()]
        # print(f"Added block Successfully")
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
            print(f"{bcolors.FAIL}Hit time Invalid{bcolors.ENDC}")
            return False
        if not validateSignature(block.getUnsignedStr(), block.generatorPubKey, block.signature):
            print(f"{bcolors.FAIL}signature invalid{bcolors.ENDC}")
            return False
        if not verifyBaseTarget(blocks, block):
            print(f"{bcolors.FAIL}base target invalid{bcolors.ENDC}")
            return False
        if not verifyCumulativeDifficulty(block, prevBlock):
            print(f"{bcolors.FAIL}cumulative difficulty invalid{bcolors.ENDC}")
            return False
        if not verifyGenerationSignature(block, prevBlock):
            print(f"{bcolors.FAIL}generation signature invalid{bcolors.ENDC}")
            return False
        if len(block.transactions)==0:
            return True

        if not self.addTxResolveDependency(block):
            print(f"{bcolors.FAIL}Invalid Transaction{bcolors.ENDC}")
            return False

        for tx in block.transactions:
            if tx.type == "currency" and not self.isCoinbase(tx):
                # if tx.getHash() not in self.transactionPool.keys():
                #     sender = self.findByTxid(tx.txIn[0].txId).txOut[tx.txIn[0].outputIndex].receiver
                #     self.addTransaction(tx, sender)
                if not self.verifyTransaction(tx, True):
                    print(f"{bcolors.FAIL} Transaction invalid{bcolors.ENDC}")
                    return False
            elif tx.type == "task":
                if tx.getHash() not in self.taskPool.keys():
                    if not self.addTask(tx):
                        print(f"{bcolors.FAIL} Task invalid{bcolors.ENDC}")
                        return False
            elif tx.type == "taskSolution":
                if tx.getHash() not in self.wstPool.keys():
                    if not self.addTaskSolution(tx):
                        print(f"{bcolors.FAIL} Task solution invalid{bcolors.ENDC}")
                        return False

        if self.hasCurrencyTransactions(block) and not self.verifyCoinbase(block):
            print(f"{bcolors.FAIL}Coinbase invalid{bcolors.ENDC}")
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
        txId = self.findByTxid(task.getHash())
        if txId is not None:
            return False
        valid = TaskService.validateTask(task)
        if not valid:
            return False
        self.taskPool[task.getHash()] = task
        self.untrainedTasks[task.getHash()] = task
        return True

    def addTaskSolution(self, taskSolution: TaskSolution) -> bool:
        task = self.findByTxid(taskSolution.taskId)
        if task == None or task.type != "task":
            return False


        if taskSolution.taskId not in self.untrainedTasks.keys():
            oldTaskSol = None
            for wstId in self.wstPool.keys():
                wst = self.wstPool[wstId]
                if wst.taskId == taskSolution.taskId:
                    oldTaskSol = wst
                    break
            if oldTaskSol == None:
                return False
            if oldTaskSol.accuracy > taskSolution.accuracy:
                return False
            valid = TaskService.validateTaskSolution(task, taskSolution)
            if not valid:
                return False
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} ValidateTaskSolution() done successfully")
            del self.wstPool[oldTaskSol.getHash()]
        else:
            valid = TaskService.validateTaskSolution(task, taskSolution)
            if not valid:
                return False
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} ValidateTaskSolution() done successfully")
            try:
                del self.untrainedTasks[taskSolution.taskId]
            except:
                print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Untrained Task already deleted")
                pass
            print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Deleted task from Untrained Tasks")
        self.wstPool[taskSolution.getHash()] = taskSolution
        print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC} Task Solution Added Successfuly")
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
        print("verify")
        coinbaseTx = block.transactions[0]
        if len(coinbaseTx.txIn) != 1 or len(coinbaseTx.txOut) != 1:
            return False
        if coinbaseTx.txIn[0].txId!="0":
            return False
        coinbaseAmt = coinbaseTx.txOut[0].amount
        txIds = [t.getHash() for t in block.transactions if t.type == "currency" and not self.isCoinbase(t)]
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
        # print(self.mainChain)
        for blockHash in self.mainChain:
            block = self.blocks[blockHash]
            # print(block)
            for transaction in block.transactions:
                txHash = transaction.getHash()
                # print(txHash,txId)
                if txHash == txId:
                    return transaction
        
        try:
            transaction = self.transactionPool[txId]["transaction"]
            return transaction
        except:
            pass

        try:
            transaction = self.taskPool[txId]
            return transaction
        except:
            pass

        try:
            transaction = self.wstPool[txId]
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
        # print("wst balance: " + str(wstBalance))
        return wstBalance

    @staticmethod
    def hasCurrencyTransactions(block: Block) -> bool:
        print("has")
        return len([t for t in block.transactions if t.type=="currency"]) > 0

    @staticmethod
    def isCoinbase(transaction: Transaction):
        return transaction.txIn[0].signature == "Coinbase Transaction"

    def addTxResolveDependency(self, block: Block) -> bool:
        transactions = [t for t in block.transactions if t.type == "currency" and not self.isCoinbase(t)]
        txIds = [t.getHash() for t in transactions]
        for i in range(len(transactions)):
            tx = transactions[i]
            for txIn in tx.txIn:
                try:
                    index = txIds.index(txIn.txId)
                    if index > i:
                        transactions[i], transactions[index] = transactions[index], transactions[i]
                        txIds[i], txIds[index] = txIds[index], txIds[i]
                except Exception as e:
                    print(e)
                    pass
        for tx in transactions:
            if tx.getHash() not in self.transactionPool.keys():
                sender = self.findByTxid(tx.txIn[0].txId).txOut[tx.txIn[0].outputIndex].receiver
                if not self.addTransaction(tx, sender):
                    return False
        return True
