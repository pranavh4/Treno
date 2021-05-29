import json
from lib.block import Block
from lib.transaction import TransactionInput,Transaction, TransactionOutput
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from argparse import ArgumentParser

from lib.blockchain import Blockchain
from lib.mining_thread import MiningThread

app = Flask(__name__)
CORS(app)



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

@app.route("/block/add")
def addBlock():
    block = blockchain.createBlock("30819f300d06092a864886f70d010101050003818d0030818902818100cb8d1b8ae3f9e568284f181f3c5fc2cf98c2e13a9f21734fa41a33bed6745e93f95c6f44e27a5f9992981c3d1bd613166f8bbf9a2245f576deb91049354635887c62eeb22969ef63a7b5fc2c53701b067dcc9425e11dac183f3328c4b64dd6493b454b09b9d24e228acd8f8795ce673b4804549a4c9de6dca9511252bb5e97530203010001")
    status = blockchain.addBlock(block)
    return jsonify({"status":status})

@app.route("/test")
def test():
    # print(blockchain.mainChain)
    print([str(blockchain.blocks[h]) for h in blockchain.mainChain])
    print(blockchain.transactionPool)
    print(blockchain.utxoPool)
    return jsonify({"status":"success"})

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("keyFilePath", help="Path of json file which stores your public and private keys")
    args = parser.parse_args()

    blockchain = Blockchain()
    blockchain.createGenesisBlock()

    with open(args.keyFilePath) as f:
        keys = json.load(f)
    
    print(keys)
    miningThread = MiningThread(blockchain, keys["publicKey"], keys["privateKey"])
    miningThread.setDaemon(True)
    miningThread.start()
    app.run(host="127.0.0.1", port=5000)

