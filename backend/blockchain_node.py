from lib.taskService import TaskService
from lib.task import Task
from lib.p2p import P2P
from lib.blockchain import Blockchain
from lib.mining_thread import MiningThread
from lib.taskThread import TaskThread
from lib.block import Block
from lib.transaction import TransactionInput,Transaction, TransactionOutput
import json
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from argparse import ArgumentParser
import time
import signal

app = Flask(__name__)
CORS(app)

seedNodeUrl = "http://127.0.0.1:8001"
blockRequestLimit = 2

@app.route("/getUtxo", methods = ['POST'])
def getUtxo():
    sender = request.json["sender"]
    return jsonify({"utxo": blockchain.utxoPool[sender]})

@app.route("/transactions/add", methods = ['POST'])
def addTransaction():
    reqData = request.json
    sender = reqData["sender"]
    transaction = reqData["transaction"]
    txIn, txOut = [],[]
    for iTx in transaction["txIn"]:
        txIn.append(TransactionInput(iTx["txId"],iTx["outputIndex"],iTx["signature"]))
    for oTx in transaction["txOut"]:
        txOut.append(TransactionOutput(oTx["amount"],oTx["receiver"]))
    transaction = Transaction(txIn,txOut)
    added = blockchain.addTransaction(transaction, sender)
    if added:
        retData = {"status": "Success"}
    else:
        retData = {"status": "Failure"}

    return jsonify(retData)

@app.route("/tasks/add", methods = ['POST'])
def addTask():
    reqData = request.json
    task = Task.fromDict(reqData)
    return {"status": blockchain.addTask(task)}

@app.route("/block/add")
def addBlock():
    block = blockchain.createBlock("30819f300d06092a864886f70d010101050003818d0030818902818100cb8d1b8ae3f9e568284f181f3c5fc2cf98c2e13a9f21734fa41a33bed6745e93f95c6f44e27a5f9992981c3d1bd613166f8bbf9a2245f576deb91049354635887c62eeb22969ef63a7b5fc2c53701b067dcc9425e11dac183f3328c4b64dd6493b454b09b9d24e228acd8f8795ce673b4804549a4c9de6dca9511252bb5e97530203010001")
    status = blockchain.addBlock(block)
    return jsonify({"status":status})

@app.route("/registerNode")
def registerNode():
    return P2P.registerNode(port)

@app.route("/deleteNode")
def deleteNode():
    return P2P.deleteNode(port)

@app.route("/pauseMining")
def pauseMining():
    miningThread.pauseMining()
    return jsonify({"isMining":miningThread.isMining})

@app.route("/continueMining")
def continueMining():
    miningThread.continueMining()
    return jsonify({"isMining":miningThread.isMining})

@app.route("/fetchBlockHeight")
def fetchBlockHeight():
    response = {}
    response["blockHeight"] = len(blockchain.mainChain)
    return response

@app.route("/fetchBlockByIndex", methods = ["POST"])
def fetchBlockByIndex():
    requestData = request.json
    index = requestData["index"]
    block = blockchain.blocks[blockchain.mainChain[index]].toDict()
    blockHash = blockchain.mainChain[index]
    return jsonify({"block":block,"hash":blockHash})

@app.route("/fetchBlocks",methods = ['POST'])
def fetchBlocks():
    requestData = request.json
    limit = requestData["limit"]
    blockHash = requestData["blockHash"]
    response = {}
    response["blocks"] = P2P.fetchBlocks(blockchain,blockHash,limit)
    return response

@app.route("/receiveBlock",methods= ["POST"])
def receiveBlock():
    requestData = request.json
    source = requestData["sender"]
    block = Block.fromDict(requestData["block"])
    print(f"Received block with Hash {block.getHash()}from {source}")
    blockchain.addBlock(block)
    return jsonify({"status":f"{port} received block successfully"})

@app.route("/getBlockChain")
def getBlockChain():
    displayLength = 4
    blocks=[]
    for ind in range(len(blockchain.mainChain)):
        blocks.append(blockchain.mainChain[ind][:displayLength])
    blockChainHeight = len(blockchain.mainChain)
    resp = {}
    resp["blocks"]=blocks
    resp["blockChainHeight"]=blockChainHeight

    return jsonify(resp)


@app.route("/test")
def test():
    # print(blockchain.mainChain)
    print([str(blockchain.blocks[h]) for h in blockchain.mainChain])
    print(blockchain.transactionPool)
    print(blockchain.utxoPool)
    return jsonify({"status":"success"})

@app.route("/printStatusLocal")
def testNew():
    displayLength=4
    print(f"BlockChain Height: {len(blockchain.mainChain)}")
    print("*"*20)
    for ind in range(len(blockchain.mainChain)):
        currentBlock = blockchain.blocks[blockchain.mainChain[ind]]
        print(f"Block Index: {ind}")
        print(f"Block Hash: {str(blockchain.mainChain[ind])[:displayLength]}")
        print(f"Previous Block Hash: {str(currentBlock.prevBlockHash)[:displayLength]}")
        if ind>0:
            timeDiff = currentBlock.timestamp - blockchain.blocks[blockchain.mainChain[ind-1]].timestamp
            print(f"Timestamp: {currentBlock.timestamp} (+{timeDiff})")
        else:
            print(f"Timestamp: {currentBlock.timestamp}")
        
        print(f"Base Target: {currentBlock.baseTarget}")
        print(f"Generation Signature: {currentBlock.generationSignature[:displayLength]}")
        print(f"Cumulative Difficulty: {currentBlock.cumulativeDifficulty}")
        print(f"Generator Public Key: {currentBlock.generatorPubKey[:displayLength]}")
        print(f"Signature: {currentBlock.signature[:displayLength]}")
        if currentBlock.transactions==[]:
            print("Transactions: Empty")
        else:
            print("Transactions:")
        for transaction in currentBlock.transactions:
            if transaction.type == "currency":
                print(f"->Type: {transaction.type}")
                print(f"->TxIn:")
                for txin in transaction.txIn:
                    print(f"---> txID: {txin.txId[:displayLength]}  outputIndex: {txin.outputIndex}  Signature: {txin.signature[:displayLength]}")
                print(f"->TxOut:")
                for txout in transaction.txOut:
                    print(f"---> Amount: {txout.amount}  Receiver: {txout.receiver[:displayLength]}")
            else:
                print(transaction)
        print("*"*20)
    return jsonify({"status":"success"})

# def handler(signum, frame):
#     msg = "Ctrl-c was pressed. Deleting Registration fromm seed_node"
#     P2P.deleteNode()
#     print(msg, end="", flush=True)
#     exit(1)
 
# signal.signal(signal.SIGINT, handler)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("keyFilePath", help="Path of json file which stores your public and private keys")
    parser.add_argument("port", help="Port to start server on")
    args = parser.parse_args()
    port = args.port
    P2P.setP2PPort(port)
    print(f"PORT: {P2P.port}")
    blockchain = Blockchain()
    blockchain.createGenesisBlock()
    seedTimestamp = P2P.getGenesisNodeTimestamp()
    print(f"Received timestamp from seed node {seedTimestamp}")
    if seedTimestamp == -1:
        currTimestamp = int(time.time())
        blockchain.GENESIS_NODE_TIMESTAMP = currTimestamp
        P2P.setGenesisNodeTimestamp(currTimestamp)
        P2P.registerNode()
    else:
        P2P.registerNode()
        blockchain.GENESIS_NODE_TIMESTAMP = seedTimestamp
    
    print(f"Global Timestamp: {blockchain.GENESIS_NODE_TIMESTAMP}")

    with open(args.keyFilePath) as f:
        keys = json.load(f)
    
    print(keys)
    
    nodes = []
    nodes = P2P.fetchNodes()
    if nodes!=[]:
        P2P.syncNode(blockchain,blockRequestLimit,nodes)
    
    miningThread = MiningThread(blockchain, keys["publicKey"], keys["privateKey"])
    miningThread.setDaemon(True)
    miningThread.start()

    TaskService.setFilePaths(port)
    taskThread = TaskThread(blockchain, keys["publicKey"], keys["privateKey"])
    taskThread.setDaemon(True)
    taskThread.start()

    

    app.run(host="127.0.0.1", port=port)
