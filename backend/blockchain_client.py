from lib.block_explorer import BlockExplorer
from lib.utils import generateSignature
from lib.task import Task
import requests
from flask import Flask, jsonify, request, render_template, Response
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


@app.route('/<path:path>',methods=['GET', 'POST'])
def proxy(path):
    if request.method=='GET':
        resp = requests.get(f'http://localhost:5000/{path}')
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in     resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
    if request.method=='POST':
        resp = requests.post(f'http://localhost:5000/{path}',json=request.get_json())
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
    return response

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000, debug=True)
