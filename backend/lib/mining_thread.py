from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from .blockchain import Blockchain

import time
from .block import Block
import threading
from hashlib import sha256
from .transaction import *
from .utils import *
import math
class MiningThread(threading.Thread):
    # FORGING_DELAY = 30

    def __init__(self, blockchain: Blockchain, publicKey: str, privateKey: str):
        super().__init__()
        self.blockchain = blockchain
        self.publicKey = publicKey
        self.privateKey = privateKey
        self.hitTime = None
        self.lastBlockId = None
        self.hitValue = None
        self.nextBaseTarget = None
        self.effectiveBalance = blockchain.getWSTBalance(len(blockchain.mainChain), publicKey)
        

    def run(self):
        threading.Timer(1, self.run).start()
        lastBlock = self.blockchain.blocks[self.blockchain.mainChain[-1]]
        # generationLimit = int(math.floor(time.time() - self.FORGING_DELAY))
        # if self.lastBlockId != lastBlock.getHash():
            # self.lastBlockId = lastBlock.getHash()
            # if lastBlock.timestamp > time.time() - 600 and lastBlock.prevBlockHash!="0":
            #     prevBlock = self.blockchain.blocks[lastBlock.prevBlockHash]
            #     self.setLastBlock(prevBlock)
            #     nextTimestamp = self.getNextTimestamp(generationLimit)
            #     if nextTimestamp!=generationLimit and nextTimestamp > generationLimit and nextTimestamp < lastBlock.timestamp:
            #         self.blockchain.popLastBlock()
            #         self.lastBlockId = prevBlock.getHash()
            #         lastBlock = prevBlock
        if self.lastBlockId != lastBlock.getHash():
            self.setLastBlock(lastBlock)
        # print(generationLimit - self.hitTime)
        # print(str(self.hitTime - lastBlock.timestamp) + " " + str(time.time() - lastBlock.timestamp))
        # print("hit vs genLim: " + str(self.hitTime) + " " + str(generationLimit))
        if self.hitTime == int(math.floor(time.time())):
            print("added block")
            block = self.createBlock()
            self.blockchain.addBlock(block)
        return 

    @staticmethod
    def getHitValue(generationSignature: str, publicKey: str) -> int:
        hashValue = sha256(bytes(generationSignature + publicKey, encoding='utf-8')).hexdigest()
        hitValue = int(hashValue[:8],16)
        return hitValue

    @staticmethod
    def getHitTime(block: Block, effectiveBalance: int, hitValue: int, target: int) -> int:
        hitTime = block.timestamp + (hitValue / (effectiveBalance * target))
        print("Hit interval: " + str(hitTime - block.timestamp))
        return int(math.floor(hitTime))

    def setLastBlock(self, block: Block):
        height = self.blockchain.mainChain.index(block.getHash()) + 1
        index = height - 4 if height - 4 > 0 else 0
        blocks = [self.blockchain.blocks[b] for b in self.blockchain.mainChain[index:height]]
        self.nextBaseTarget = self.getNextBaseTarget(blocks)
        print("next base target: " + str(self.nextBaseTarget))
        self.effectiveBalance = self.blockchain.getWSTBalance(self.blockchain.mainChain.index(block.getHash()), self.publicKey)
        self.hitValue = self.getHitValue(block.generationSignature, self.publicKey)
        self.lastBlockId = block.getHash()
        self.hitTime =  self.getHitTime(block, self.effectiveBalance, self.hitValue, self.nextBaseTarget)

    def getNextTimestamp(self, generationLimit) -> int:
        return generationLimit if generationLimit - self.hitTime > 3600 else self.hitTime + 1

    def createBlock(self) -> Block:
        txIds = self.blockchain.transactionPool.keys()
        taskIds = self.blockchain.taskPool.keys()
        wstIds = self.blockchain.wstPool.keys()
        prevBlock = self.blockchain.blocks[self.blockchain.mainChain[-1]]
        prevBlockHash = prevBlock.getHash()
        blockTransactions = []
        # height = self.blockchain.mainChain.index(prevBlockHash) + 1
        # index = height - 4 if height - 4 > 0 else 0
        block = Block(
            [],
            prevBlockHash,
            self.publicKey,
            self.getNextGenerationSignature(prevBlock, self.publicKey),
            self.nextBaseTarget,
            self.getNextCumulativeDifficulty(prevBlock.cumulativeDifficulty, self.nextBaseTarget),
            self.hitTime
            )
        # blocks = [self.blockchain.blocks[b] for b in self.blockchain.mainChain[index:height]] + [block]
        # while len(blocks)!=4:
        #     if blocks[0].prevBlockHash == "0":
        #         break
        #     b = self.blockchain.blocks[blocks[0].prevBlockHash]
        #     blocks = [b] + blocks
        # baseTarget = self.getNextBaseTarget(blocks)
        # block.baseTarget = self.baseTarget
        # block.cumulativeDifficulty = self.getNextCumulativeDifficulty(prevBlock.cumulativeDifficulty, baseTarget)
        if len(txIds) == 0:
            block.signBlock(self.privateKey)
            return block

        if len(txIds) != 0:
            sortedTransactions = sorted(
                [self.blockchain.transactionPool[txId] for txId in txIds],
                key = lambda t:t["transactionFee"], 
                reverse=True
            )
            currencyTransactions = [t["transaction"] for t in sortedTransactions[:self.blockchain.MAX_CURRENCY_TRANSACTION_IN_BLOCK]]

            minerReward = sum([t["transactionFee"] for t in sortedTransactions[:self.blockchain.MAX_CURRENCY_TRANSACTION_IN_BLOCK]])
            coinbaseTransaction = Transaction(
                [TransactionInput("0",-1,"Coinbase Transaction")],
                [TransactionOutput(minerReward, self.publicKey)]
            )
            blockTransactions += [coinbaseTransaction] + currencyTransactions

        taskRequests = []
        wstTransactions = []
        if len(wstIds) != 0:
            wstTransactions = sorted([self.blockchain.wstPool[wstId] for wstId in wstIds], key=lambda t:t.timestamp)[:self.blockchain.MAX_WST_IN_BLOCK]
            taskRequests += [self.blockchain.taskPool[wst.taskId] for wst in wstTransactions]
        
        if len(taskIds) != 0 and len(taskRequests) < self.blockchain.MAX_TASK_REQUESTS_IN_BLOCK:
            maxTasks = self.blockchain.MAX_TASK_REQUESTS_IN_BLOCK - len(taskRequests)
            remainingTasks = [self.blockchain.taskPool[k] for k in self.blockchain.taskPool.keys() if k not in [wst.taskId for wst in wstTransactions]]
            taskRequests += remainingTasks[:maxTasks]
        
        block.transactions = blockTransactions + wstTransactions + taskRequests
        block.signBlock(self.privateKey)
        return block 

    @staticmethod
    def getNextGenerationSignature(prevBlock: Block, publicKey: str) -> str:
        s = prevBlock.generationSignature + publicKey
        return sha256(bytes(s, encoding='utf-8')).hexdigest()

    @staticmethod
    def getNextBaseTarget(blocks: list[Block], MAXRATIO = 67, MINRATIO = 53, GAMMA = 0.64) -> int:
        if len(blocks) != 1:
            s = 0
            for i in range(len(blocks) - 1):
                s += blocks[i + 1].timestamp - blocks[i].timestamp
            s /= len(blocks)
        else:
            s = 60
        tp = blocks[-1].baseTarget
        if s > 60:
            return int((tp * min(s, MAXRATIO))/60)
        else:
            return int(tp - (tp * GAMMA*(60 - max(s, MINRATIO)))/60)

    @staticmethod
    def getNextCumulativeDifficulty(prevCD, baseTarget) -> int:
        return int(prevCD + (pow(2,64)/baseTarget))