from lib.block_explorer import BlockExplorer
from lib.task import TaskSolution
from lib.taskService import TaskService
from lib.task import Task
from lib.p2p import P2P
from lib.blockchain import Blockchain
from lib.mining_thread import MiningThread
from lib.taskThread import TaskThread
from lib.block import Block
from lib.utils import bcolors
from lib.transaction import TransactionInput,Transaction, TransactionOutput
import json
import requests
from threading import get_ident
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from argparse import ArgumentParser
import time
import signal
import sys 

app = Flask(__name__)
CORS(app)

seedNodeUrl = "http://127.0.0.1:8001"
blockRequestLimit = 2

@app.route("/getUtxo", methods = ['POST'])
def getUtxo():
    sender = request.json["sender"]
    utxo = []
    try:
        utxo = blockchain.utxoPool[sender]
    except:
        pass
    return jsonify({"utxo": utxo})

@app.route("/transactions/add", methods = ['POST'])
def addTransaction():
    reqData = request.json
    sender = reqData["sender"]
    transaction = Transaction.fromDict(reqData["transaction"])
    print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC}Received transaction with sender {sender[:4]} from {reqData['from']}")
    added = blockchain.addTransaction(transaction, sender)
    if added:
        if reqData["from"]=="client":
            P2P.broadcastTransaction(transaction,sender)
        retData = {"status": "Success"}
    else:
        retData = {"status": "Failure"}

    return jsonify(retData)

@app.route("/tasks/add", methods = ['POST'])
def addTask():
    reqData = request.json
    task = Task.fromDict(reqData["task"])
    print(f"Received task from {reqData['from']}")
    added = blockchain.addTask(task)
    if added:
        if reqData['from']=='client':
            P2P.broadcastTask(task)
        retData = {"status": "Success"}
    else:
        retData = {"status": "Failure"}
    return jsonify(retData)

@app.route("/taskSolutions/add", methods = ['POST'])
def addTaskSolution():
    reqData = request.json
    taskSolution = TaskSolution.fromDict(reqData["taskSolution"])
    print(f"Received task solution from {reqData['source']}")
    added = blockchain.addTaskSolution(taskSolution)
    if added:
        retData = {"status" : "Success"}
    else:
        retData = {"status" : "Failure"}
    return jsonify(retData)


@app.route("/block/add")
def addBlock():
    block = blockchain.createBlock("30819f300d06092a864886f70d010101050003818d0030818902818100cb8d1b8ae3f9e568284f181f3c5fc2cf98c2e13a9f21734fa41a33bed6745e93f95c6f44e27a5f9992981c3d1bd613166f8bbf9a2245f576deb91049354635887c62eeb22969ef63a7b5fc2c53701b067dcc9425e11dac183f3328c4b64dd6493b454b09b9d24e228acd8f8795ce673b4804549a4c9de6dca9511252bb5e97530203010001")
    status = blockchain.addBlock(block)
    return jsonify({"status":status})

@app.route("/registerNode")
def registerNode():
    return P2P.registerNode()

@app.route("/deleteNode")
def deleteNode():
    return P2P.deleteNode()

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
    print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC}Returning {len(response['blocks'])} blocks for fetchBlocks")
    return response

@app.route("/receiveBlock",methods= ["POST"])
def receiveBlock():
    requestData = request.json
    source = requestData["sender"]
    block = Block.fromDict(requestData["block"])
    print(f"Received block with Hash {block.getHash()} from {source}")
    added = blockchain.addBlock(block)
    if added:
        print(f"{bcolors.OKGREEN}({P2P.port}) Added remote block {block.getHash()} received from {source}{bcolors.ENDC}")
        retData = {"status" : "Success"}
    else:
        retData = {"status": "Failure" }
    return jsonify(retData)

@app.route("/getBlockChain")
def getBlockChain():
    displayLength = 4
    blocks=[]
    for ind in range(len(blockchain.mainChain)):
        blocks.append(blockchain.mainChain[ind][displayLength:])
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
    displayLength=-6
    
    print("*"*20)
    for ind in range(len(blockchain.mainChain)):
        currentBlock = blockchain.blocks[blockchain.mainChain[ind]]
        print(f"Block Index: {ind}")
        print(f"{bcolors.UNDERLINE}Block Hash:{bcolors.ENDC} {str(blockchain.mainChain[ind])[displayLength:]}")
        print(f"{bcolors.UNDERLINE}Previous Block Hash:{bcolors.ENDC} {str(currentBlock.prevBlockHash)[displayLength:]}")
        if ind>0:
            timeDiff = currentBlock.timestamp - blockchain.blocks[blockchain.mainChain[ind-1]].timestamp
            print(f"Timestamp: {currentBlock.timestamp} (+{bcolors.WARNING}{timeDiff}{bcolors.ENDC})")
        else:
            print(f"Timestamp: {currentBlock.timestamp}")
        
        print(f"Base Target: {currentBlock.baseTarget}")
        print(f"Generation Signature: {currentBlock.generationSignature[displayLength:]}")
        print(f"Cumulative Difficulty: {currentBlock.cumulativeDifficulty}")
        print(f"Generator Public Key: {currentBlock.generatorPubKey[displayLength:]}")
        print(f"Signature: {currentBlock.signature[displayLength:]}")
        if currentBlock.transactions==[]:
            print(f"{bcolors.FAIL}Transactions: Empty{bcolors.ENDC}")
        else:
            print("Transactions:")
        for transaction in currentBlock.transactions:
            if transaction.type == "currency":
                print(f"{bcolors.HEADER}->Type: {bcolors.OKGREEN}{transaction.type}{bcolors.ENDC}")
                print(f"->TxIn:")
                for txin in transaction.txIn:
                    print(f"---> txID: {txin.txId[displayLength:]}  outputIndex: {txin.outputIndex}  Signature: {txin.signature[displayLength:]}")
                print(f"->TxOut:")
                for txout in transaction.txOut:
                    print(f"---> Amount: {txout.amount}  Receiver: {txout.receiver[displayLength:]}")
            elif transaction.type == "task":
                print(f"{bcolors.HEADER}->Type: {bcolors.OKBLUE}{transaction.type}{bcolors.ENDC}")
                print(f"Resource URL: {transaction.resourceURL}")
                print(f"Threshold: {transaction.threshold}")
                print(f"Max epochs: {transaction.maxEpochs}")
                print(f"Public Key: {transaction.publicKey[displayLength:]}")
                print(f"Signature: {transaction.signature[displayLength:]}")
            elif transaction.type == "taskSolution":
                print(f"{bcolors.HEADER}->Type: {bcolors.OKCYAN}{transaction.type}{bcolors.ENDC}")
                print(f"--->Task ID: {transaction.taskId}")
                print(f"--->Model URL: {transaction.modelURL}")
                print(f"--->Accuracy: {transaction.accuracy}")
                print(f"--->WST: {transaction.wst}")
                print(f"--->Public Key: {transaction.publicKey[displayLength:]}")
                print(f"--->Signature: {transaction.signature[displayLength:]}")
        print("*"*20)
    print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC}{bcolors.HEADER}BlockChain Height: {len(blockchain.mainChain)}{bcolors.ENDC}")
    return jsonify({"status":"success"})

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)





# Block Explorer Endpoints
@app.route("/get/blocks")
def getBlocks():
    endHeight = request.args.get("endHeight", -1)
    numBlocks = request.args.get("numBlocks", -1)
    blocks = blockExplorer.getBlocks(endHeight, numBlocks)
    return jsonify({"blocks": blocks})

@app.route("/get/transactions")
def getTransactions():
    publicKey = request.args.get("publicKey", None)
    retData = blockExplorer.getTransactions(publicKey)
    return jsonify(retData)  

@app.route("/get/wst")
def getWST():
    publicKey = request.args.get("publicKey", None)
    retData = blockExplorer.getWSTTransactions(publicKey)
    return jsonify(retData)   

@app.route("/get/tasks")
def getTasks():
    publicKey = request.args.get("publicKey", None)
    retData = blockExplorer.getTasks(publicKey)
    return jsonify(retData)

@app.route("/get/balance")
def getBalance():
    publicKey = request.args.get("publicKey", None)
    retData = blockExplorer.getBalance(publicKey)
    return jsonify(retData)

@app.route("/get/wstBalance")
def getWstBalance():
    publicKey = request.args.get("publicKey", None)
    retData = blockExplorer.getWSTBalance(publicKey)
    return jsonify(retData)

if __name__ == "__main__":

    signal.signal(signal.SIGBREAK, signal_handler)
    # signal.pause()
    parser = ArgumentParser()
    parser.add_argument("keyFilePath", help="Path of json file which stores your public and private keys")
    parser.add_argument("port", help="Port to start server on")
    args = parser.parse_args()
    port = args.port
    TaskService.setFilePaths(port)
    P2P.setP2PPort(port)
    print(f"PORT: {P2P.port}")
    blockchain = Blockchain()
    blockchain.createGenesisBlock()
    seedTimestamp = P2P.getGenesisNodeTimestamp()
    print(f"{bcolors.OKGREEN}Received timestamp from seed node {seedTimestamp}{bcolors.ENDC}")
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
    
    nodes = []
    nodes = P2P.fetchNodes()
    if nodes!=[]:
        P2P.syncNode(blockchain,blockRequestLimit,nodes)
    
    blockExplorer = BlockExplorer(blockchain)
    
    miningThread = MiningThread(blockchain, keys["publicKey"], keys["privateKey"])
    miningThread.setDaemon(True)
    miningThread.start()

    
    taskThread = TaskThread(blockchain, keys["publicKey"], keys["privateKey"])
    taskThread.setDaemon(True)
    taskThread.start()

    app.run(host="127.0.0.1", port=port)
