import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json
import sys
sys.path.append('./backend')
from lib.wallet import Wallet

app = Flask(__name__)
CORS(app)

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
    retData = requests.post('http://localhost:5000/transactions/add', json=transaction)
    return retData.json()

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000)
