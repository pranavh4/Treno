from lib.block_explorer import BlockExplorer
from lib.utils import generateSignature
from lib.task import Task
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json
import sys
sys.path.append('./backend')
from lib.wallet import Wallet

app = Flask(__name__)
CORS(app)


@app.route('/generate/keys')
def generateKeys():
    return jsonify(Wallet.generateKey())


@app.route('/generate/transaction', methods=['POST'])
def generateTransaction():
    reqData = request.json
    utxo = requests.post('http://localhost:5000/getUtxo', json={"sender":reqData["sender"]}).json()["utxo"]
    print(utxo)
    transaction = Wallet.createTransaction(
        utxo,
        reqData["sender"],
        reqData["receiver"],
        reqData["amount"],
        reqData["transactionFee"],
        reqData["privateKey"]
    )
    print(transaction)
    retData = requests.post('http://localhost:5000/transactions/add', json={"sender":reqData["sender"], "transaction": transaction})
    return retData.json()

@app.route('/generate/task', methods = ['POST'])
def generateTask():
    reqData = request.json
    task = Task(
        reqData["resourceUrl"],
        reqData["threshold"],
        reqData["maxEpochs"],
        reqData["publicKey"],
        ""
    )
    task.signature = generateSignature(task.getUnsignedStr(), reqData["privateKey"])
    print(task)
    return requests.post('http://localhost:5000/tasks/add', json=json.loads(str(task))).json()

@app.route('/get/blocks')
def getBlocks():
    endHeight = request.args.get("endHeight", -1)
    numBlocks = request.args.get("numBlocks", 10)
    return jsonify(BlockExplorer.getBlocks(endHeight, numBlocks))

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000, debug=True)
