from .block import Block
from hashlib import sha256
from pathlib import Path
from .transaction import Transaction, TransactionInput, TransactionOutput
from .utils import validateSignature
import json


class Blockchain:
    MAX_COINS = 5000000
    MIN_TRANSACTION_FEE = 1
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
        print(transaction)
        block = Block([transaction],"0")
        blockHash = block.getHash()

        self.blocks = {blockHash: block}
        self.mainChain = [blockHash]
        self.utxoPool[genesisKey["publicKey"]] = [{
            "txId": transaction.getHash(),
            "outputIndex": 0,
            "amount": self.MAX_COINS
        }]
        
    def addBlock(self, block) -> bool:
        blockHash = block.getHash()
        self.mainChain.append(blockHash)
        self.blocks[blockHash] = block

    def verifyTransaction(self, transaction) -> bool:
        inputAmt = 0
        for input in transaction.txIn:
            inputTx = self.findByTxid(input.txId)
            if inputTx == None:
                print("no input tx")
                return False
            outputTx = inputTx.txOut[input.outputIndex]
            signer = outputTx.receiver
            if not validateSignature(inputTx, signer, input.signature):
                print("signature not valid")
                return False
            if self.utxoSpent(inputTx):
                print("utxo already spent")
                return False
            inputAmt += outputTx.amount
        
        if inputAmt > self.MAX_COINS:
            print("Input greater than max coins")
            return False
        
        outputAmt = 0
        for outputTx in transaction.txOut:
            outputAmt += outputTx.amount
        
        if inputAmt < outputAmt:
            print("Insufficient Funds")
            return False
        
        if (inputAmt - outputAmt) < self.MIN_TRANSACTION_FEE:
            print("No transaction fees")
            return False
        
        return True

    def utxoSpent(self, inputTx) -> bool:
        for blockHash in self.mainChain:
            block = self.blocks[blockHash]
            for transaction in block.transactions:
                for iTx in transaction.txIn:
                    if inputTx == iTx:
                        return True

        for key in self.transactionPool.keys():
            transaction = self.transactionPool[key]
            for iTx in transaction.txIn:
                if inputTx == iTx:
                    return True
    
        return False

    def findByTxid(self, txId) -> Transaction:
        for blockHash in self.mainChain:
            block = self.blocks[blockHash]
            for transaction in block.transactions:
                txHash = sha256(bytes(str(transaction),encoding='utf-8')).hexdigest()
                if txHash == txId:
                    return transaction
        return None