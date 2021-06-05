from .task import TaskSolution
from .blockchain import Blockchain

class BlockExplorer():
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain

    def getBlocks(self, endHeight: int, numBlocks: int):
        #endHeight - height of the block, if -1 it'll be most recent block height
        #startHeight will be endHeight - minBlocks
        if endHeight == -1:
            endHeight = len(self.blockchain.mainChain)
        startHeight = endHeight - numBlocks
        if startHeight < 0:
            startHeight = 0
        blocks = [self.blockchain.blocks[self.blockchain.mainChain[i]] for i in self.blockchain.mainChain[startHeight:endHeight]]
        return {"blocks": blocks}

    def getTransactions(self, publicKey: str) -> dict:
        transactions = []
        balance = -1
        for bId in self.blockchain.mainChain:
            block = self.blockchain.blocks[bId]
            for tx in block.transactions:
                if tx.type == "currency":
                    # print("transaction = " + str(tx))
                    if self.blockchain.isCoinbase(tx):
                        if publicKey and tx.txOut[0].receiver != publicKey:
                            continue
                        transactions.append({
                            "sender": "Coinbase",
                            "receiver": tx.txOut[0].receiver,
                            "amount": tx.txOut[0].amount,
                            "transactionFee": "NA",
                            "timestamp": block.timestamp
                        })
                    else:
                        if tx.txIn[0].outputIndex == -1:
                            for txOut in tx.txOut:
                                receiver = txOut.receiver
                                if publicKey and publicKey!= receiver:
                                    continue
                                amount = txOut.amount
                                transactions.append({
                                    "sender": "Genesis",
                                    "receiver": receiver,
                                    "amount": amount,
                                    "transactionFee": "NA",
                                    "timestamp": block.timestamp
                                })

                        else:
                            sender = self.blockchain.findByTxid(tx.txIn[0].txId).txOut[tx.txIn[0].outputIndex].receiver
                            print("sender" + str(sender))
                            inpAmt = 0
                            outAmt = 0
                            receivers = [txOut.receiver for txOut in tx.txOut]
                            if publicKey and publicKey not in [sender] + receivers:
                                continue
                            for txIn in tx.txIn:
                                iTx = self.blockchain.findByTxid(txIn.txId)
                                inpAmt += iTx.txOut[txIn.outputIndex].amount

                            for txOut in tx.txOut:
                                outAmt += txOut.amount
                                if txOut.receiver != sender:
                                    receiver = txOut.receiver
                                    amount = txOut.amount
                            transactions.append({
                                "sender": sender,
                                "receiver": receiver,
                                "amount": amount,
                                "transactionFee": inpAmt - outAmt,
                                "timestamp": block.timestamp
                            })
        
        if publicKey:
            balance = 0
            try:
                utxos = self.blockchain.utxoPool[publicKey]
                for utxo in utxos:
                    balance += utxo["amount"]
            except:
                pass

        return {"balance": balance, "transactions": transactions}

    def getWSTTransactions(self, publicKey: str) -> dict:
        transactions = []
        balance = -1
        for bId in self.blockchain.mainChain:
            block = self.blockchain.blocks[bId]
            for tx in block.transactions:
                if tx.type == "taskSolution":
                    if publicKey and publicKey != tx.publicKey:
                        continue
                    transactions.append(tx.toDict())
        
        if publicKey:
            balance = 0
            for tx in transactions:
                balance += tx["wst"]
        
        return {"balance": balance, "wst": transactions}

    def getTasks(self, publicKey: str) -> dict:
        tasks = []
        for bId in self.blockchain.mainChain:
            block = self.blockchain.blocks[bId]
            for tx in block.transactions:
                if tx.type == "task":
                    if publicKey and publicKey != tx.publicKey:
                        continue
                    taskSolution = self.findTaskSolutionByTaskId(tx.getHash())
                    if taskSolution:
                        taskSolution = taskSolution.toDict()
                    tasks.append({
                        "task": tx.toDict(),
                        "taskSolution": taskSolution
                    })
        return {"tasks": tasks}
    
    def findTaskSolutionByTaskId(self, taskId: str) -> TaskSolution:
        for bId in self.blockchain.mainChain:
            block = self.blockchain.blocks[bId]
            for tx in block.transactions:
                if tx.type == "taskSolution":
                    if tx.taskId == taskId:
                        return tx
        return None
