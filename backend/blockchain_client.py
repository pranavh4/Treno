from lib.utils import generateSignature
from lib.task import Task
import requests
from flask import Flask, jsonify, request, render_template, Response
from flask_cors import CORS
from lib.wallet import Wallet

app = Flask(__name__)
CORS(app)


@app.route('/generate/keys')
def generateKeys():
    return jsonify(Wallet.generateKey())


@app.route('/generate/transaction', methods=['POST'])
def generateTransaction():
    reqData = request.json
    node = requests.get(url='http://localhost:8001/getRandomNode').json()["node"]
    utxoPayload = {}
    utxoPayload["sender"] = reqData["sender"]
    utxo = requests.post(f'http://{node}/getUtxo', json=utxoPayload).json()["utxo"]
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
    transactionPayload = {}
    transactionPayload["sender"] = reqData["sender"]
    transactionPayload["transaction"] = transaction.toDict()
    transactionPayload["from"] = "client"
    retData = requests.post(f'http://{node}/transactions/add', json=transactionPayload)
    return retData.json()

@app.route('/generate/task', methods = ['POST'])
def generateTask():
    node = requests.get(url='http://localhost:8001/getRandomNode').json()["node"]
    reqData = request.json
    task = Task(
        reqData["resourceURL"],
        reqData["threshold"],
        reqData["maxEpochs"],
        reqData["publicKey"],
        ""
    )
    task.signature = generateSignature(task.getUnsignedStr(), reqData["privateKey"])
    payload = {}
    payload["task"] = task.toDict()
    payload["from"] = "client"
    retData = requests.post(f'http://{node}/tasks/add', json=payload) 
    return retData.json()


@app.route('/<path:path>',methods=['GET', 'POST'])
def proxy(path):
    url = f'http://localhost:5000/{path}'
        
    if request.method=='GET':
        url += "?"
        for param in request.args.keys():
            url += param + "=" + request.args.get(param)
        print(url)
        resp = requests.get(url)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
    if request.method=='POST':
        resp = requests.post(url,json=request.get_json())
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
    return response

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000, debug=True)
